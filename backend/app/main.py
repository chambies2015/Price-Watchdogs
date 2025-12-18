from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.api import auth, services, snapshots, subscriptions, health, metrics
from app.scheduler import start_scheduler, shutdown_scheduler
from app.config import settings
from app.middleware.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
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


@app.get("/")
async def root():
    return {"message": "Price Watchdogs API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
