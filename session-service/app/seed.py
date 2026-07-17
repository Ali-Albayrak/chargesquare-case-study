"""Baseline seed data separated from idempotent insert logic."""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import User, Wallet

logger = logging.getLogger(__name__)

USERS = [
    {"id": 7, "display_name": "Demo User"},
]

WALLETS = [
    {
        "user_id": 7,
        "balance": Decimal("500.00"),
        "currency": "TRY",
    },
]


def seed_baseline(db: Session) -> None:
    """Idempotent ensure of user 7 + wallet 500.00 TRY. Never overwrites live wallet balance."""
    inserted = 0

    for row in USERS:
        if db.get(User, row["id"]) is None:
            db.add(User(**row))
            logger.debug(f"Inserted user {row['id']}")
            inserted += 1

    for row in WALLETS:
        existing = db.query(Wallet).filter(Wallet.user_id == row["user_id"]).first()
        if existing is None:
            db.add(Wallet(**row))
            logger.debug(f"Inserted wallet {row['user_id']}")
            inserted += 1

    db.commit()
    logger.info(
        "Seed complete — users=%s wallets=%s inserted=%s",
        len(USERS),
        len(WALLETS),
        inserted,
    )
