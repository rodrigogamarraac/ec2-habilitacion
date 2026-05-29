from http import HTTPStatus
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from src.models.session_filters import SessionFilters
from src.models.session_schema import SessionDetailOut, SessionOut, SessionPage
from src.providers.session_providers import get_session_service
from src.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/search/", response_model=list[SessionOut])
async def search_sessions(
    query: str = Query(...),
    service: SessionService = Depends(get_session_service),
):
    sessions = await service.search_sessions(query)
    return sessions

@router.get("/", response_model=SessionPage)
async def list_sessions(
    filters: SessionFilters = Depends(),
    service: SessionService = Depends(get_session_service),
):
    sessions = await service.get_sessions(filters)
    return sessions


@router.get("/{session_id}", response_model=SessionDetailOut)
async def get_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
):
    session = await service.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="session not found")

    return session
