"""Baseline seed data separated from idempotent insert logic."""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import AuthAccount, Role, User, Wallet

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

# Demo passwords (plaintext only for seed input; stored hashed).
AUTH_ACCOUNTS = [
    {"username": "viewer", "password": "viewer", "role": Role.VIEWER.value},
    {"username": "admin", "password": "admin", "role": Role.ADMIN.value},
]


def seed_baseline(db: Session) -> None:
    """Idempotent ensure of user 7 + wallet + demo auth accounts. Never overwrites live wallet balance."""
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

    for row in AUTH_ACCOUNTS:
        existing = db.query(AuthAccount).filter(AuthAccount.username == row["username"]).first()
        if existing is None:
            db.add(
                AuthAccount(
                    username=row["username"],
                    password_hash=hash_password(row["password"]),
                    role=row["role"],
                )
            )
            logger.debug(f"Inserted auth account {row['username']}")
            inserted += 1

    db.commit()
    logger.info(
        "Seed complete — users=%s wallets=%s auth=%s inserted=%s",
        len(USERS),
        len(WALLETS),
        len(AUTH_ACCOUNTS),
        inserted,
    )
