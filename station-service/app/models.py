import enum
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ConnectorStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    connectors: Mapped[list["Connector"]] = relationship(back_populates="station")


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    price_per_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    start_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    connectors: Mapped[list["Connector"]] = relationship(back_populates="tariff")


class Connector(Base):
    __tablename__ = "connectors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False, index=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    power_kw: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    # native_enum=False → VARCHAR (works with SQLite tests and Postgres without CREATE TYPE)
    status: Mapped[ConnectorStatus] = mapped_column(
        Enum(ConnectorStatus, name="connector_status", native_enum=False),
        nullable=False,
        default=ConnectorStatus.AVAILABLE,
    )

    station: Mapped[Station] = relationship(back_populates="connectors")
    tariff: Mapped[Tariff] = relationship(back_populates="connectors")
