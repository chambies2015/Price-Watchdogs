from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.api import auth, services, snapshots, subscriptions, health, metrics
from app.scheduler import start_scheduler, shutdown_scheduler
from app.config import settings
from app.middleware.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from pathlib import Path
import logging
import os
import json

if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1 if settings.environment == "production" else 1.0,
    )

if settings.environment == "production":
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Price Watchdogs API", version="1.0.0")
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )

cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(services.dashboard_router)
app.include_router(snapshots.router)
app.include_router(subscriptions.router)
app.include_router(health.router)
app.include_router(metrics.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

frontend_build_path = Path(__file__).parent.parent.parent / "frontend" / "out"
logger.info(f"Looking for frontend build at: {frontend_build_path}")
logger.info(f"Frontend build path exists: {frontend_build_path.exists()}")

if frontend_build_path.exists():
    logger.info("Frontend build found, setting up static file serving")
    static_assets_path = frontend_build_path / "_next" / "static"
    if static_assets_path.exists():
        app.mount("/_next/static", StaticFiles(directory=str(static_assets_path)), name="static")
        logger.info(f"Mounted static assets at: {static_assets_path}")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            return JSONResponse({"detail": "Not found"}, status_code=404)
        
        if full_path.startswith("_next/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        
        file_path = frontend_build_path / full_path
        
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        if file_path.exists() and file_path.is_dir():
            index_in_dir = file_path / "index.html"
            if index_in_dir.exists():
                return FileResponse(index_in_dir)
        
        index_path = frontend_build_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return JSONResponse({"detail": "Not found"}, status_code=404)
else:
    logger.warning(f"Frontend build not found at {frontend_build_path}. Frontend will not be served.")
    @app.get("/")
    async def root():
        return {"message": "Price Watchdogs API - Frontend not built. Run 'cd frontend && npm run build'"}


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    start_scheduler()
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()
    logger.info("Application shutdown complete")
