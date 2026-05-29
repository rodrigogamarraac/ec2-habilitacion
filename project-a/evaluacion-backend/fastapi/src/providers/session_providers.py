from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_db_session
from src.db.redis import get_redis
from src.repositories.session_repository import SessionRepository
from src.services.session_service import SessionService

def get_session_repository(database_session: AsyncSession = Depends(get_db_session)) -> SessionRepository:
    return SessionRepository(database_session)

def get_session_service(
    session_repository: SessionRepository = Depends(get_session_repository),
    redis_client = Depends(get_redis),
) -> SessionService:
    return SessionService(session_repository, redis_client)
