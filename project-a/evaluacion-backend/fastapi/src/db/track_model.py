import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base

class TrackModel(Base):
    __tablename__ = "track"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    conference_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("content.conference.id"))
    name: Mapped[str] = mapped_column()
    color: Mapped[str | None] = mapped_column()
    description: Mapped[str | None] = mapped_column()
