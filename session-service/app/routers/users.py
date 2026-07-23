import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import Principal, get_current_principal, require_roles
from app.db import get_db
from app.errors import AppError
from app.models import Role, User, Wallet
from app.schemas import SessionOut, TopUpRequest, WalletOut
from app.services import session_service
from app.wallet import credit

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.get("/users/{user_id}/sessions", response_model=list[SessionOut])
def list_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(get_current_principal),
) -> list[SessionOut]:
    return session_service.list_sessions_for_user(db, user_id)


@router.get("/users/{user_id}/wallet", response_model=WalletOut)
def get_wallet(
    user_id: int,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(get_current_principal),
) -> WalletOut:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if wallet is None:
        raise AppError(
            status_code=404,
            error="USER_NOT_FOUND",
            message=f"Wallet for user {user_id} was not found",
        )
    return WalletOut(userId=user_id, balance=wallet.balance, currency=wallet.currency)


@router.post("/users/{user_id}/wallet/top-up", response_model=WalletOut)
def top_up_wallet(
    user_id: int,
    body: TopUpRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_roles(Role.ADMIN)),
) -> WalletOut:
    if db.get(User, user_id) is None:
        raise AppError(
            status_code=404,
            error="USER_NOT_FOUND",
            message=f"User {user_id} was not found",
        )
    balance = credit(db, user_id, body.amount)
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).one()
    db.commit()
    logger.info(
        "Wallet topped up actor=%s user_id=%s amount=%s balance_after=%s",
        principal.username,
        user_id,
        body.amount,
        balance,
    )
    return WalletOut(userId=user_id, balance=balance, currency=wallet.currency)
