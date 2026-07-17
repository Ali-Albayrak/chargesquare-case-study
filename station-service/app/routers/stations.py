from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ConnectorOut
from app.services import station_service

router = APIRouter(tags=["stations"])


@router.get("/stations/{station_id}/connectors", response_model=list[ConnectorOut])
def list_station_connectors(station_id: int, db: Session = Depends(get_db)) -> list[ConnectorOut]:
    return station_service.list_station_connectors(db, station_id)
