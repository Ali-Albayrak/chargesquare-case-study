import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.clients.station_client import StationClient, station_client
from app.errors import AppError
from app.models import ChargingSession, SessionStatus, User
from app.schemas import SessionOut, StartSessionRequest, StopSessionRequest, TariffSnapshotOut
from app.services.cost import calculate_cost
from app.wallet import debit, get_balance

logger = logging.getLogger(__name__)


def _to_session_out(
    session: ChargingSession,
    wallet_balance_after: Decimal | None = None,
) -> SessionOut:
    return SessionOut(
        sessionId=session.id,
        userId=session.user_id,
        connectorId=session.connector_id,
        status=SessionStatus(session.status),
        startedAt=session.started_at,
        endedAt=session.ended_at,
        energyKwh=session.energy_kwh,
        cost=session.cost,
        currency=session.snapshot_currency,
        walletBalanceAfter=wallet_balance_after,
        tariffSnapshot=TariffSnapshotOut(
            tariffId=session.snapshot_tariff_id,
            pricePerKwh=session.snapshot_price_per_kwh,
            startFee=session.snapshot_start_fee,
            currency=session.snapshot_currency,
        ),
    )


def _current_wallet_balance(db: Session, user_id: int) -> Decimal | None:
    return get_balance(db, user_id)


def start_session(
    db: Session,
    request: StartSessionRequest,
    client: StationClient | None = None,
) -> SessionOut:
    client = client or station_client

    user = db.get(User, request.user_id)
    if user is None:
        raise AppError(
            status_code=404,
            error="USER_NOT_FOUND",
            message=f"User {request.user_id} was not found",
        )

    connector = client.get_connector(request.connector_id)
    # TODO: use enum instead of magic string
    if connector.status != "AVAILABLE":
        raise AppError(
            status_code=409,
            error="CONNECTOR_OCCUPIED",
            message=f"Connector {request.connector_id} is not AVAILABLE",
        )

    client.occupy(request.connector_id)

    session = ChargingSession(
        user_id=request.user_id,
        connector_id=request.connector_id,
        status=SessionStatus.ACTIVE.value,
        started_at=datetime.now(timezone.utc),
        snapshot_price_per_kwh=connector.price_per_kwh,
        snapshot_start_fee=connector.start_fee,
        snapshot_currency=connector.currency,
        snapshot_tariff_id=connector.tariff_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(
        "Session started session_id=%s user_id=%s connector_id=%s",
        session.id,
        session.user_id,
        session.connector_id,
    )
    return _to_session_out(session)


def stop_session(
    db: Session,
    session_id: int,
    request: StopSessionRequest,
    client: StationClient | None = None,
) -> SessionOut:
    client = client or station_client

    session = db.get(ChargingSession, session_id)
    if session is None:
        raise AppError(
            status_code=404,
            error="SESSION_NOT_FOUND",
            message=f"Session {session_id} was not found",
        )
    if session.status != SessionStatus.ACTIVE.value:
        raise AppError(
            status_code=409,
            error="SESSION_NOT_ACTIVE",
            message=f"Session {session_id} is not ACTIVE",
        )

    cost = calculate_cost(
        request.energy_kwh,
        session.snapshot_price_per_kwh,
        session.snapshot_start_fee,
    )

    balance_after = debit(db, session.user_id, cost)

    session.status = SessionStatus.COMPLETED.value
    session.ended_at = datetime.now(timezone.utc)
    session.energy_kwh = request.energy_kwh
    session.cost = cost
    db.add(session)
    db.commit()
    db.refresh(session)

    client.release(session.connector_id)

    logger.info(
        "Session stopped session_id=%s energy_kwh=%s",
        session.id,
        session.energy_kwh,
    )
    logger.info("Cost charged session_id=%s cost=%s", session.id, session.cost)
    logger.info(
        "Wallet debited user_id=%s amount=%s balance_after=%s",
        session.user_id,
        cost,
        balance_after,
    )
    return _to_session_out(session, wallet_balance_after=balance_after)


def get_session(db: Session, session_id: int) -> SessionOut:
    session = db.get(ChargingSession, session_id)
    if session is None:
        raise AppError(
            status_code=404,
            error="SESSION_NOT_FOUND",
            message=f"Session {session_id} was not found",
        )
    balance = None
    if session.status == SessionStatus.COMPLETED.value:
        balance = _current_wallet_balance(db, session.user_id)
    return _to_session_out(session, wallet_balance_after=balance)


def list_sessions_for_user(db: Session, user_id: int) -> list[SessionOut]:
    sessions = (
        db.query(ChargingSession)
        .filter(ChargingSession.user_id == user_id)
        .order_by(ChargingSession.id.asc())
        .all()
    )
    result: list[SessionOut] = []
    for session in sessions:
        balance = None
        if session.status == SessionStatus.COMPLETED.value:
            # TODO: why get current balance for each session? should be done once at the end of the list_sessions_for_user function
            balance = _current_wallet_balance(db, session.user_id)
        result.append(_to_session_out(session, wallet_balance_after=balance))
    return result
