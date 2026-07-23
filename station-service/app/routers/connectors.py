from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import Principal, Role, get_current_principal, require_roles
from app.db import get_db
from app.schemas import ConnectorOut, ConnectorStatusOut
from app.services import connector_service

router = APIRouter(tags=["connectors"])


@router.get("/connectors/{connector_id}", response_model=ConnectorOut)
def get_connector(
    connector_id: int,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(get_current_principal),
) -> ConnectorOut:
    return connector_service.get_connector(db, connector_id)


@router.post("/connectors/{connector_id}/occupy", response_model=ConnectorStatusOut)
def occupy_connector(
    connector_id: int,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(require_roles(Role.ADMIN)),
) -> ConnectorStatusOut:
    return connector_service.occupy_connector(db, connector_id)


@router.post("/connectors/{connector_id}/release", response_model=ConnectorStatusOut)
def release_connector(
    connector_id: int,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(require_roles(Role.ADMIN)),
) -> ConnectorStatusOut:
    return connector_service.release_connector(db, connector_id)
