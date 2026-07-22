from decimal import Decimal

from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Wallet


def debit(db: Session, user_id: int, amount: Decimal) -> Decimal:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if wallet is None:
        raise AppError(
            status_code=404,
            error="USER_NOT_FOUND",
            message=f"Wallet for user {user_id} was not found",
        )
    # Reject: no negative balance (session stays ACTIVE).
    if wallet.balance < amount:
        raise AppError(
            status_code=409,
            error="INSUFFICIENT_BALANCE",
            message=f"Wallet balance {wallet.balance} is insufficient for cost {amount}",
        )
    wallet.balance = wallet.balance - amount
    db.add(wallet)
    return wallet.balance
