from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import SessionOut
from app.services import session_service

router = APIRouter(tags=["users"])


@router.get("/users/{user_id}/sessions", response_model=list[SessionOut])
def list_user_sessions(user_id: int, db: Session = Depends(get_db)) -> list[SessionOut]:
    return session_service.list_sessions_for_user(db, user_id)
