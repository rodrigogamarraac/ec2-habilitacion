from django.db import models
from .base import Base
from .session import Session
from .speaker import Speaker

class SessionSpeaker(Base):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="session_speakers"
    )
    speaker = models.ForeignKey(
        Speaker, on_delete=models.CASCADE, related_name="session_speakers"
    )

    class Meta:
        db_table = '"content"."session_speaker"'
        unique_together = [("session", "speaker")]

    def __str__(self):
        return f"{self.session} — {self.speaker}"
