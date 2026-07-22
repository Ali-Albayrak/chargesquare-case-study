import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.db import Base, SessionLocal, engine
from app.errors import AppError, app_error_handler, validation_error_handler
from app.routers import health, sessions, users
from app.seed import seed_baseline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_baseline(db)
        logger.info("Session Service schema + seed ready")
    finally:
        db.close()
    yield


app = FastAPI(title="ChargeSquare Session Service", lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)


app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(users.router)
