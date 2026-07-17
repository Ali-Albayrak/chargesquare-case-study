import logging

from sqlalchemy.orm import Session, joinedload

from app.errors import AppError
from app.models import Connector, ConnectorStatus
from app.schemas import ConnectorOut, ConnectorStatusOut, TariffOut

logger = logging.getLogger(__name__)


def to_connector_out(connector: Connector) -> ConnectorOut:
    tariff = connector.tariff
    return ConnectorOut(
        connectorId=connector.id,
        stationId=connector.station_id,
        type=connector.type,
        powerKw=connector.power_kw,
        status=connector.status,
        tariff=TariffOut(
            tariffId=tariff.id,
            pricePerKwh=tariff.price_per_kwh,
            startFee=tariff.start_fee,
            currency=tariff.currency,
        ),
    )


def get_connector_or_404(db: Session, connector_id: int) -> Connector:
    connector = (
        db.query(Connector)
        .options(joinedload(Connector.tariff))
        .filter(Connector.id == connector_id)
        .first()
    )
    if connector is None:
        raise AppError(
            status_code=404,
            error="CONNECTOR_NOT_FOUND",
            message=f"Connector {connector_id} was not found",
        )
    return connector


def get_connector(db: Session, connector_id: int) -> ConnectorOut:
    return to_connector_out(get_connector_or_404(db, connector_id))


def occupy_connector(db: Session, connector_id: int) -> ConnectorStatusOut:
    connector = get_connector_or_404(db, connector_id)
    if connector.status == ConnectorStatus.OCCUPIED:
        raise AppError(
            status_code=409,
            error="CONNECTOR_OCCUPIED",
            message=f"Connector {connector_id} is not AVAILABLE",
        )
    connector.status = ConnectorStatus.OCCUPIED
    db.commit()
    db.refresh(connector)
    logger.info("Connector occupied connector_id=%s status=%s", connector_id, connector.status)
    return ConnectorStatusOut(connector_id=connector.id, status=connector.status)


def release_connector(db: Session, connector_id: int) -> ConnectorStatusOut:
    connector = get_connector_or_404(db, connector_id)
    connector.status = ConnectorStatus.AVAILABLE
    db.commit()
    db.refresh(connector)
    logger.info("Connector released connector_id=%s status=%s", connector_id, connector.status)
    return ConnectorStatusOut(connector_id=connector.id, status=connector.status)
