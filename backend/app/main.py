from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from backend.app.core.settings import settings
    from backend.app.api.endpoints import health
except ImportError:
    from app.core.settings import settings
    from app.api.endpoints import health

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}
