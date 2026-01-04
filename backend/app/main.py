"""
FastAPI application entry point

PRIVACY SAFEGUARDS:
- Request bodies are NEVER logged (especially for /predict endpoint)
- Personal user data is processed in-memory only
- No user data is written to database or logs
- SQLite is READ-ONLY for course/feature lookup
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import time

from .config import settings
from .models.ml_models import model_cache
from .routers import health, courses, predictions

# Configure logging - PRIVACY: Do NOT log request bodies
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable uvicorn access log for request bodies
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events

    Startup:
    - Load ML models into memory
    - Verify database connection

    Shutdown:
    - Cleanup resources
    """
    # Startup
    logger.info("Starting up application...")

    # Load models once at startup
    try:
        logger.info("Loading ML models...")
        model_cache.load_models(settings.MODELS_DIR)
        logger.info(f"Successfully loaded {model_cache.get_model_count()} models")
    except Exception as e:
        logger.error(f"Failed to load models: {str(e)}")
        raise

    # Verify database exists
    if not settings.DB_PATH.exists():
        logger.error(f"Database not found at {settings.DB_PATH}")
        raise FileNotFoundError(f"Database not found at {settings.DB_PATH}")
    else:
        logger.info(f"Database found at {settings.DB_PATH}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# PRIVACY MIDDLEWARE: Log only method, path, and status - NEVER log request bodies
@app.middleware("http")
async def privacy_preserving_logging(request: Request, call_next):
    """
    Custom middleware to log requests WITHOUT exposing request bodies.
    This ensures personal user data in POST /predict is never logged.
    """
    start_time = time.time()

    # Process request (body is NOT read here, so it's not logged)
    response = await call_next(request)

    # Log only: method, path, status, duration
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - "
        f"Duration: {process_time:.3f}s"
    )

    return response


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    health.router,
    prefix=settings.API_V1_PREFIX,
    tags=["health"]
)

app.include_router(
    courses.router,
    prefix=settings.API_V1_PREFIX,
    tags=["courses"]
)

app.include_router(
    predictions.router,
    prefix=settings.API_V1_PREFIX,
    tags=["predictions"]
)

# Mount static files for plots
if settings.PLOTS_DIR.exists():
    app.mount("/static/plots", StaticFiles(directory=str(settings.PLOTS_DIR)), name="plots")
    logger.info(f"Mounted static plots directory: {settings.PLOTS_DIR}")
else:
    logger.warning(f"Plots directory not found: {settings.PLOTS_DIR}")

# In production: Serve React frontend build
if settings.ENVIRONMENT == "production":
    if settings.FRONTEND_BUILD_DIR.exists():
        # Mount static assets (JS, CSS, images)
        app.mount("/assets", StaticFiles(directory=str(settings.FRONTEND_BUILD_DIR / "assets")), name="assets")

        # Catch-all route: serve index.html for all non-API routes (SPA routing)
        from fastapi.responses import FileResponse

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """
            Serve React SPA for all routes that aren't API endpoints.
            This enables React Router to work on page refresh.
            """
            # If path starts with /api, let it fall through to 404
            if full_path.startswith("api/"):
                return {"detail": "Not Found"}

            # Serve index.html for all other routes (React Router handles them)
            index_file = settings.FRONTEND_BUILD_DIR / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            else:
                return {"detail": "Frontend not found"}

        logger.info(f"Mounted frontend build directory: {settings.FRONTEND_BUILD_DIR}")
    else:
        logger.warning(f"Frontend build directory not found: {settings.FRONTEND_BUILD_DIR}")
else:
    # In development: Return API information at root
    @app.get("/")
    async def root():
        """
        Root endpoint - Development only

        Returns API information for testing
        """
        return {
            "message": "UC Berkeley Course Difficulty Prediction API",
            "version": settings.VERSION,
            "docs": "/docs",
            "api": settings.API_V1_PREFIX
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
