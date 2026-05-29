from datetime import datetime, timezone
from uuid import UUID
from src.models.speaker_schema import SpeakerDetailOut, SessionSummary, SpeakerOut

class SpeakerService:
    def __init__(self, speaker_repository, redis_client = None):
        self.speaker_repository = speaker_repository
        self.redis_client = redis_client

    async def get_speaker(self, speaker_id: UUID) -> SpeakerDetailOut | None:
        cache_key = f"speaker:{speaker_id}"
        cached_data = await self._try_get_cache(cache_key)

        if cached_data:
            return SpeakerDetailOut.model_validate_json(cached_data)

        speaker = await self.speaker_repository.get_speaker_by_id(speaker_id)

        if not speaker:
            return None

        now = datetime.now(timezone.utc)
        next_sessions = []
        past_sessions_count = 0

        for session in speaker.sessions:
            if session.starts_at > now:
                next_sessions.append(session)
            else:
                past_sessions_count += 1

        next_sessions.sort(key=lambda s: s.starts_at)
        next_sessions = next_sessions[:10]

        result = SpeakerDetailOut(
            id = speaker.id,
            name=speaker.name,
            affiliation= speaker.affiliation or "",
            next_sessions=[
                SessionSummary(
                    id=s.id,
                    title=s.title,
                    starts_at=s.starts_at
                ) for s in next_sessions
            ],
            past_sessions_count=past_sessions_count
        )

        await self._try_set_cache(cache_key, result.model_dump_json())
        return result

    async def get_all_speakers(self) -> list[SpeakerOut]:
        speakers = await self.speaker_repository.get_all_speakers()
        return [SpeakerOut.model_validate(speaker) for speaker in speakers]

    async def get_speakers_with_upcoming(self) -> list[SpeakerOut]:
        speakers = await self.speaker_repository.get_speakers_with_upcoming()
        return [SpeakerOut.model_validate(speaker) for speaker in speakers]

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