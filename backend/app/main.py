"""
Gatimaan FastAPI Application Entry Point
AI-Powered Railway Block Planning System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, tasks, trains, blocks, analytics, import_data, ml

app = FastAPI(
    title="Gatimaan API",
    description=(
        "AI-Powered Automatic Block Planning for Railway Maintenance. "
        "PROTOTYPE — Uses synthetic simulated data. Not connected to real IR systems."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(tasks.router, prefix="/tasks", tags=["Maintenance Tasks"])
app.include_router(trains.router, prefix="/trains", tags=["Train Schedule"])
app.include_router(blocks.router, prefix="/blocks", tags=["Block Planning"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(import_data.router, prefix="/import", tags=["Data Import"])
app.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Gatimaan API",
        "version": "1.0.0",
        "prototype": True,
        "data_note": "SIMULATED_PROTOTYPE_DATA — Not real Indian Railways data",
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Gatimaan — AI-Powered Railway Block Planning API",
        "docs": "/docs",
        "prototype_note": "This is an SIH prototype using synthetic simulated data.",
    }
