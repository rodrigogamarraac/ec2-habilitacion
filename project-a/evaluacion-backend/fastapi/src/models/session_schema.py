from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from src.models.speaker_schema import SpeakerOut
from src.models.track_schema import TrackOut

class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    starts_at: datetime
    ends_at: datetime
    capacity: int | None = None
    speakers: list[SpeakerOut] = []
    track: TrackOut

class SessionDetailOut(SessionOut):
    abstract: str

class SessionPage(BaseModel):
    count: int
    results: list[SessionOut]
