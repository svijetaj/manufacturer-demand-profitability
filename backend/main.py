"""
Main FastAPI Application for Meridian Corp Demand & Profitability Intelligence Platform.
Exposes REST endpoints for Next.js frontend, analytics, ML simulation, and RAG knowledge extraction.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import filters, overview, demand, margins, opex, predict, rag

app = FastAPI(
    title="Meridian Corp — Demand & Profitability Intelligence API",
    description="Enterprise REST API for DuckDB analytical semantic layers, LightGBM/MLP forecasting, and CVP profitability modeling.",
    version="2.0.0"
)

# Enable CORS for the Next.js frontend.
# A wildcard origin combined with allow_credentials=True is rejected by browsers
# and, if it were honored, would let any site issue credentialed requests. Pin to
# explicit origins instead, configurable via CORS_ALLOW_ORIGINS (comma-separated)
# for production deployments.
_DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register sub-routers
app.include_router(filters.router)
app.include_router(overview.router)
app.include_router(demand.router)
app.include_router(margins.router)
app.include_router(opex.router)
app.include_router(predict.router)
app.include_router(rag.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Meridian Corp Intelligence API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": "finance.duckdb"}
