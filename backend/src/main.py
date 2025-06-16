"""
FastAPI backend for Manugen AI project.
"""

import os

# read version number from manugen_ai package
from importlib.metadata import version

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adk_api import adk_app  # Import the ADK FastAPI app

MANUGEN_VERSION = version("manugen_ai")

# Create FastAPI app
app = FastAPI(
    title="Manugen AI Backend",
    description="A backend for the Manugen AI project, providing APIs for AI-driven manuscript generation.",
    version=MANUGEN_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint returning basic API information."""
    return {
        "message": "Welcome to Manugen AI Backend",
        "version": MANUGEN_VERSION,
        "docs": "/docs",
        "adk_api_docs": "/adk_api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "manugen-ai-backend"}


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint."""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": ["manuscript_generation", "ai_agents"],
    }


# mount the ADK FastAPI app as a sub-app of our API server
app.mount(
    "/adk_api",
    adk_app,
    name="adk_agents",
)

if __name__ == "__main__":
    # This allows running the app directly with python
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("MANUGEN_API_PORT", 8000)),
        reload=True,
        log_level="info",
    )
