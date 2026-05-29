from django.db import models
from .base import Base
from .track import Track
from .speaker import Speaker

class Session(Base):
    track = models.ForeignKey(
        Track, on_delete=models.CASCADE, related_name="sessions"
    )
    title = models.CharField(max_length=300)
    abstract = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    speakers = models.ManyToManyField(
        Speaker,
        through="SessionSpeaker",
        related_name="sessions",
        blank=True,
    )

    class Meta:
        db_table = '"content"."session"'
        ordering = ["starts_at"]

    def __str__(self):
        return self.title
