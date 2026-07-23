import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class Role(str, enum.Enum):
    VIEWER = "VIEWER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    wallet: Mapped["Wallet | None"] = relationship(back_populates="user", uselist=False)
    sessions: Mapped[list["ChargingSession"]] = relationship(back_populates="user")


class AuthAccount(Base):
    """Demo login accounts — not a real user directory."""

    __tablename__ = "auth_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (UniqueConstraint("user_id", name="uq_wallets_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    user: Mapped[User] = relationship(back_populates="wallet")


class ChargingSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    connector_id: Mapped[int] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=SessionStatus.ACTIVE.value)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    energy_kwh: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    wallet_balance_after: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    snapshot_price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    snapshot_start_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    snapshot_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    snapshot_tariff_id: Mapped[int] = mapped_column(nullable=False)

    user: Mapped[User] = relationship(back_populates="sessions")
