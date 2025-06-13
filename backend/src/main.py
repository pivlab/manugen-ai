"""
FastAPI backend for Manugen AI project.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Create FastAPI app
app = FastAPI(
    title="Manugen AI Backend",
    description="A backend for the Manugen AI project, providing APIs for AI-driven manuscript generation.",
    version="0.1.0",
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
        "version": "0.1.0",
        "docs": "/docs",
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


if __name__ == "__main__":
    # This allows running the app directly with python
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("MANUGEN_API_PORT", 8000)),
        reload=True,
        log_level="info",
    )
