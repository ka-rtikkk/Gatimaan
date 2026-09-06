"""
Gatimaan Backend Entry Point
Run with: uvicorn run:app --reload --host 0.0.0.0 --port 8000
"""
from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
