from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ConnectorOut, ConnectorStatusOut
from app.services import connector_service

router = APIRouter(tags=["connectors"])


@router.get("/connectors/{connector_id}", response_model=ConnectorOut)
def get_connector(connector_id: int, db: Session = Depends(get_db)) -> ConnectorOut:
    return connector_service.get_connector(db, connector_id)


@router.post("/connectors/{connector_id}/occupy", response_model=ConnectorStatusOut)
def occupy_connector(connector_id: int, db: Session = Depends(get_db)) -> ConnectorStatusOut:
    return connector_service.occupy_connector(db, connector_id)


@router.post("/connectors/{connector_id}/release", response_model=ConnectorStatusOut)
def release_connector(connector_id: int, db: Session = Depends(get_db)) -> ConnectorStatusOut:
    return connector_service.release_connector(db, connector_id)
