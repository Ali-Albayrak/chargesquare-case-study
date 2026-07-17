from sqlalchemy.orm import Session, joinedload

from app.errors import AppError
from app.models import Connector, Station
from app.schemas import ConnectorOut
from app.services.connector_service import to_connector_out


def list_station_connectors(db: Session, station_id: int) -> list[ConnectorOut]:
    station = db.get(Station, station_id)
    if station is None:
        raise AppError(
            status_code=404,
            error="STATION_NOT_FOUND",
            message=f"Station {station_id} was not found",
        )

    connectors = (
        db.query(Connector)
        .options(joinedload(Connector.tariff))
        .filter(Connector.station_id == station_id)
        .order_by(Connector.id)
        .all()
    )
    return [to_connector_out(c) for c in connectors]
