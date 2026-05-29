from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SpeakerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    affiliation: int = 0

class SessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    starts_at: datetime


class SpeakerDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    affiliation: str = ""
    next_sessions: list[SessionSummary] = []
    past_sessions_count: int = 0

class SpeakerPage(BaseModel):
    count: int
    results: list[SpeakerOut]
