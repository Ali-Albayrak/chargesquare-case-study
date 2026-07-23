from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import Principal, get_current_principal
from app.db import get_db
from app.schemas import SessionOut, StartSessionRequest, StopSessionRequest
from app.services import session_service

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=SessionOut, status_code=201)
def create_session(
    body: StartSessionRequest,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(get_current_principal),
) -> SessionOut:
    return session_service.start_session(db, body)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def read_session(
    session_id: int,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(get_current_principal),
) -> SessionOut:
    return session_service.get_session(db, session_id)


@router.post("/sessions/{session_id}/stop", response_model=SessionOut)
def stop_session(
    session_id: int,
    body: StopSessionRequest,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(get_current_principal),
) -> SessionOut:
    return session_service.stop_session(db, session_id, body)
