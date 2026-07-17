"""Wallet module boundary — sync in-process debit/settle."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Wallet
from app.wallet.service import debit

__all__ = ["get_balance", "debit"]


def get_balance(db: Session, user_id: int) -> Decimal | None:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if wallet is None:
        return None
    return wallet.balance
