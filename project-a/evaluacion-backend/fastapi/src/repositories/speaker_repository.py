from uuid import UUID
from datetime import datetime
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.session_model import SessionModel
from src.db.speaker_model import SpeakerModel

class SpeakerRepository:
    def __init__(self, database_session: AsyncSession):
        self.database_session = database_session

    async def get_speaker_by_id(self, speaker_id: UUID) -> SpeakerModel | None:
        query = (
            select(SpeakerModel)
            .where(SpeakerModel.id == speaker_id)
            .options(selectinload(SpeakerModel.sessions))
        )

        return (await self.database_session.execute(query)).scalar_one_or_none()

    async def get_all_speakers(self) -> list[SpeakerModel]:
        query = select(SpeakerModel).options(selectinload(SpeakerModel.sessions))
        return (await self.database_session.execute(query)).scalars().all()

    async def get_speakers_with_upcoming(self) -> list[SpeakerModel]:
        query = (
            select(SpeakerModel)
            .join(SpeakerModel.sessions)
            .where(SessionModel.starts_at > func.now())
            .distinct()
            .options(selectinload(SpeakerModel.sessions))
        )

        return (await self.database_session.execute(query)).scalars().all()
