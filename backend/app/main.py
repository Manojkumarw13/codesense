from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from backend.app.core.settings import settings
from backend.app.api.endpoints import health, events
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestIDMiddleware
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.database import SessionLocal
from backend.app.services.processing import EventProcessor

# Initialize logging
setup_logging()
logger = logging.getLogger("codesense.main")

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

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

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}

# Background Processing Job
async def process_events_loop():
    logger.info("Starting background event processing loop...")
    while True:
        try:
            db = SessionLocal()
            processor = EventProcessor(db)
            count = processor.process_pending_events(limit=50)
            db.close()
            
            if count > 0:
                logger.info(f"Processed {count} events in background job.")
            else:
                # Sleep longer if no events to process
                await asyncio.sleep(5)
                continue
                
        except Exception as e:
            logger.error(f"Error in background processing loop: {e}")
            
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_events_loop())

