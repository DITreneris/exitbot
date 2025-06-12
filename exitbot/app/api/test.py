"""
Test endpoints that don't require database access
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def test_endpoint():
    """
    Simple test endpoint that doesn't require the database
    """
    return {
        "status": "ok",
        "message": "Test endpoint is working",
        "data": {
            "test_id": 12345,
            "is_functional": True,
            "features": ["interviews", "sentiment_analysis", "reporting"],
        },
    }


@router.get("/ping")
async def ping():
    """
    Simple health check endpoint
    """
    return {"ping": "pong"}
