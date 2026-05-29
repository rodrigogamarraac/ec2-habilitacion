from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_db_session
from src.db.redis import get_redis
from src.repositories.speaker_repository import SpeakerRepository
from src.services.speaker_service import SpeakerService

def get_speaker_repository(database_session: AsyncSession = Depends(get_db_session)) -> SpeakerRepository:
    return SpeakerRepository(database_session)
    
def get_speaker_service(
    speaker_repository: SpeakerRepository = Depends(get_speaker_repository),
    redis_client = Depends(get_redis),
) -> SpeakerService:
    return SpeakerService(speaker_repository, redis_client)


