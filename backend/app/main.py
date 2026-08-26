from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from backend.app.core.settings import settings
from backend.app.api.endpoints import health, events, metrics as metrics_endpoint, risk
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestIDMiddleware
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.database import SessionLocal
from backend.app.services.processing import EventProcessor
from backend.app.core.observability import PrometheusMiddleware, setup_tracing
from backend.app.core.redis import get_redis_client

# Initialize logging
setup_logging()
logger = logging.getLogger("codesense.main")

# Setup OpenTelemetry tracing (no-op if unavailable)
if settings.ENABLE_TRACING:
    setup_tracing(service_name=settings.APP_NAME)

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Prometheus middleware (Phase 2 observability) — must be outermost
if settings.ENABLE_METRICS:
    app.add_middleware(PrometheusMiddleware)

# Request ID Tracking
app.add_middleware(RequestIDMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
register_exception_handlers(app)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(events.router, prefix=settings.API_V1_STR, tags=["events"])
app.include_router(metrics_endpoint.router, prefix=settings.API_V1_STR, tags=["observability"])
app.include_router(risk.router, prefix=settings.API_V1_STR, tags=["risk"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}

# Background Processing Job — uses asyncio; Celery replaces this when broker available
async def process_events_loop():
    logger.info("Starting background event processing loop...")
    while True:
        try:
            from backend.app.worker.base import run_once

            def _job():
                db = SessionLocal()
                try:
                    processor = EventProcessor(db)
                    return processor.process_pending_events(limit=50)
                finally:
                    db.close()

            count = run_once(_job, job_name="event_processor")

            if count == 0:
                # No events to process – back off
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in background processing loop: {e}")
            await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    # Probe Redis (non-blocking; falls back to in-memory automatically)
    if settings.ENABLE_REDIS:
        r = get_redis_client()
        if r:
            logger.info("Redis is available")
        else:
            logger.warning("Redis not reachable – using in-memory cache/queue fallback")

    # Start background event processor loop
    asyncio.create_task(process_events_loop())
    logger.info(f"{settings.APP_NAME} started (env={settings.APP_ENV})")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{settings.APP_NAME} shutting down")
