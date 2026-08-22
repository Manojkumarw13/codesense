from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.settings import settings
from backend.app.api.endpoints import health, events
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestIDMiddleware
from backend.app.core.exceptions import register_exception_handlers

# Initialize logging
setup_logging()

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
