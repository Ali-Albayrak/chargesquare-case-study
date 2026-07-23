from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
import logging

from app.auth import create_access_token, verify_password
from app.config import settings
from app.db import get_db
from app.errors import AppError
from app.models import AuthAccount

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: str
    password: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    role: str
    expires_in: int = Field(alias="expiresIn")


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    account = db.query(AuthAccount).filter(AuthAccount.username == body.username).first()
    if account is None or not verify_password(body.password, account.password_hash):
        logger.info("Login failed username=%s", body.username)
        raise AppError(status_code=401, error="UNAUTHORIZED", message="Invalid username or password")

    token = create_access_token(username=account.username, role=account.role)
    logger.info("Login success username=%s role=%s", account.username, account.role)
    return LoginResponse(
        accessToken=token,
        tokenType="bearer",
        role=account.role,
        expiresIn=settings.jwt_expire_minutes * 60,
    )
