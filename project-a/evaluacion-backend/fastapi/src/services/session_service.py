from uuid import UUID
from src.models.session_filters import SessionFilters
from src.models.session_schema import SessionDetailOut, SessionOut, SessionPage

class SessionService:
    def __init__(self, session_repository, redis_client=None):
        self.session_repository = session_repository
        self.redis_client = redis_client

    async def get_sessions(self, filters: SessionFilters) -> SessionPage:
        cache_key = f"sessions:{filters.search_query}:{filters.track_id}:{filters.day}:{filters.timezone}:{filters.page}:{filters.page_size}"
        cached_data = await self._try_get_cache(cache_key)

        if cached_data:
            return SessionPage.model_validate_json(cached_data)

        total_count, session_list = await self.session_repository.get_sessions(filters)
        result = SessionPage(count=total_count, results=[SessionOut.model_validate(session) for session in session_list])

        await self._try_set_cache(cache_key, result.model_dump_json())
        
        return result

    async def get_session(self, session_id: UUID) -> SessionDetailOut | None:
        cache_key = f"session:{session_id}"
        cached_data = await self._try_get_cache(cache_key)

        if cached_data:
            return SessionDetailOut.model_validate_json(cached_data)

        session = await self.session_repository.get_session_by_id(session_id)

        if not session:
            return None

        result = SessionDetailOut.model_validate(session)
        await self._try_set_cache(cach_key, result.model_dump_json())

        return result

    async def search_sessions(self, search_query: str) -> list[SessionOut]:
        sessions = await self.session_repository.search_sessions(search_query)
        return [SessionOut.model_validate(session) for session in sessions]

    async def _try_get_cache(self, cache_key: str) -> str | None:
        if not self.redis_client:
            return None
        try:
            return await self.redis_client.get(cache_key)
        except Exception:
            return None

    async def _try_set_cache(self, cache_key: str, json_value: str) -> None:
        if not self.redis_client:
            return
        try:
            await self.redis_client.setex(cache_key, 60, json_value)
        except Exception:
            pass
