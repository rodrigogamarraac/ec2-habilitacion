from uuid import UUID
from fastapi import Query

class SessionFilters:
    def __init__(
        self,
        search_query: str | None = Query(None, alias="q"),
        track_id: UUID | None = Query(None, alias="track"),
        day: str | None = None,
        timezone: str = Query("UTC", alias="tz"),
        page: int = 1,
        page_size: int = 12,
    ):
        self.search_query = search_query
        self.track_id = track_id
        self.day = day
        self.timezone = timezone
        self.page = page
        self.page_size = page_size
