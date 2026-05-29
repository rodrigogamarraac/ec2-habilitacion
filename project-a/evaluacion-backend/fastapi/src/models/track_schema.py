from uuid import UUID
from pydantic import BaseModel, ConfigDict

class TrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str = "#6f1d1b"
    description: str = ""

class TrackListOut(TrackOut):
    session_count: int = 0
