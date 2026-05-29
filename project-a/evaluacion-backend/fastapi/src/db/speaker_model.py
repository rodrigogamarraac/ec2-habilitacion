import uuid
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

_speaker_session_assoc = Table(
    "session_speaker",
    Base.metadata,
    Column("session_id", PG_UUID, ForeignKey("content.session.id")),
    Column("speaker_id", PG_UUID, ForeignKey("content.speaker.id")),
    schema="content",
)

class SpeakerModel(Base):
    __tablename__ = "speaker"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    affiliation: Mapped[str | None] = mapped_column()
    
    sessions: Mapped[list["SessionModel"]] = relationship(
        secondary=_speaker_session_assoc,
        viewonly=True,
    )
