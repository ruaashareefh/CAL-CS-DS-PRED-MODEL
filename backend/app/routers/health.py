"""
Health check endpoints
"""
from fastapi import APIRouter
from ..models.schemas import HealthResponse
from ..models.ml_models import model_cache
from ..database.connection import test_connection

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns system status including:
    - Overall health status
    - Database connectivity
    - Model loading status
    - Number of loaded models

    Returns:
        HealthResponse: Health status information
    """
    # Check database connection
    db_connected = test_connection()

    # Check model loading status
    models_loaded = model_cache.is_loaded()
    model_count = model_cache.get_model_count()

    # Overall status
    status = "healthy" if (db_connected and models_loaded) else "unhealthy"

    return HealthResponse(
        status=status,
        database_connected=db_connected,
        models_loaded=models_loaded,
        model_count=model_count
    )
