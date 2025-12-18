from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import auth, services, snapshots, subscriptions
from app.scheduler import start_scheduler, shutdown_scheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Price Watchdogs API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(services.dashboard_router)
app.include_router(snapshots.router)
app.include_router(subscriptions.router)


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
async def health():
    return {"status": "healthy"}
