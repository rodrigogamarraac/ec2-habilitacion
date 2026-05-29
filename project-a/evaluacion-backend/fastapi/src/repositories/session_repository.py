import datetime
from uuid import UUID
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.types import Date
from src.db.session_model import SessionModel
from src.models.session_filters import SessionFilters

class SessionRepository:
    def __init__(self, database_session: AsyncSession):
        self.database_session = database_session

    async def get_sessions(self, filters: SessionFilters) -> tuple[int, list]:
        base_query = self._build_filtered_query(filters)

        total_count = await self.database_session.scalar(
            select(func.count()).select_from(base_query.subquery())
        )

        session_list = (await self.database_session.execute(
            base_query
            .options(selectinload(SessionModel.track), selectinload(SessionModel.speakers))
            .order_by(SessionModel.starts_at)
            .limit(filters.page_size)
            .offset((filters.page - 1) * filters.page_size)
        )).scalars().all()

        return total_count, session_list

    async def get_session_by_id(self, session_id: UUID) -> SessionModel | None:
        query = (
            select(SessionModel)
            .options(selectinload(SessionModel.track), selectinload(SessionModel.speakers))
            .where(SessionModel.id == session_id)
        )

        return (await self.database_session.execute(query)).scalar_one_or_none()

    async def search_sessions(self, search_query: str) -> list[SessionModel]:
        search_pattern = f"%{search_query}%"
        query = (
            select(SessionModel)
            .options(selectinload(SessionModel.track), selectinload(SessionModel.speakers))
            .where(SessionModel.title.ilike(search_pattern) | SessionModel.abstract.ilike(search_pattern))
            .order_by(SessionModel.starts_at)
            .limit(50)
        )

        return (await self.database_session.execute(query)).scalars().all()

    def _build_filtered_query(self, filters: SessionFilters):
        query = select(SessionModel)

        if filters.search_query:
            search_pattern = f"%{filters.search_query}%"
            query = query.where(
                SessionModel.title.ilike(search_pattern) | SessionModel.abstract.ilike(search_pattern)
            )

        if filters.track_id:
            query = query.where(SessionModel.track_id == filters.track_id)
            
        if filters.day:
            local_date = cast(func.timezone(filters.timezone, SessionModel.starts_at), Date)
            query = query.where(local_date == datetime.date.fromisoformat(filters.day))
        
        return query

