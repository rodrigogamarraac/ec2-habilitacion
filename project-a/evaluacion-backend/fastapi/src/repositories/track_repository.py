from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session_model import SessionModel
from src.db.track_model import TrackModel

class TrackRepository:
    def __init__(self, database_session: AsyncSession):
        self.database_session = database_session

    async def get_all_tracks(self) -> list:
        query = (
            select(TrackModel, func.count(SessionModel.id).label("session_count"))
            .outerjoin(SessionModel, SessionModel.track_id == TrackModel.id)
            .group_by(TrackModel.id)
            .order_by(TrackModel.name)
        )

        return (await self.database_session.execute(query)).all()
