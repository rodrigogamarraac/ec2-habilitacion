from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_db_session
from src.repositories.track_repository import TrackRepository
from src.services.track_service import TrackService

def get_track_repository(database_session: AsyncSession = Depends(get_db_session)) -> TrackRepository:
    return TrackRepository(database_session)

def get_track_service(track_repository: TrackRepository = Depends(get_track_repository)) -> TrackService:
    return TrackService(track_repository)
