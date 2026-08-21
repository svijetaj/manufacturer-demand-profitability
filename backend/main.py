"""
Main FastAPI Application for Meridian Corp Demand & Profitability Intelligence Platform.
Exposes REST endpoints for Next.js frontend, analytics, ML simulation, and RAG knowledge extraction.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import filters, overview, demand, margins, opex, predict, rag, variance

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup pre-warming for ML predictions
    try:
        from backend.routers.predict import _compute_predict_demand_cached, _compute_predict_profitability_cached
        _compute_predict_demand_cached("neural_network", 6, 0.0, 0.0, 0.0, None, None, None)
        _compute_predict_profitability_cached(6, 0.0, 0.0, "Units Produced", 0.0, 0.0, None, None, None)
        print("ML Prediction endpoints pre-warmed successfully!")
    except Exception as e:
        print("Warm-up exception:", e)
    yield

app = FastAPI(
    title="Meridian Corp — Demand & Profitability Intelligence API",
    description="Enterprise REST API for DuckDB analytical semantic layers, LightGBM/MLP forecasting, and CVP profitability modeling.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend (local development + production Vercel domains)
_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://frontend-woad-pi-rive4dnu2e.vercel.app",
]

env_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
if env_origins:
    ALLOWED_ORIGINS = [o.strip() for o in env_origins.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
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
app.include_router(variance.router)

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
