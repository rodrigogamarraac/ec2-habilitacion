from src.models.track_schema import TrackListOut

class TrackService:
    def __init__(self, track_repository):
        self.track_repository = track_repository

    async def get_tracks(self) -> list[TrackListOut]:
        return [
            TrackListOut(
                id=track_model.id,
                name=track_model.name,
                color=track_model.colour or "#6f1d1b",
                description=track_model.description or "",
                session_count=session_count or 0,
            )
            for track_model, session_count in await self.track_repository.get_all_tracks()
        ]
