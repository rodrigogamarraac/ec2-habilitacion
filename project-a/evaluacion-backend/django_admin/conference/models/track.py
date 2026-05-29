from django.db import models
from .base import Base
from .conference import Conference

class Track(Base):
    conference = models.ForeignKey(
        Conference, on_delete=models.CASCADE, related_name="tracks"
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, blank=True, default="#6f1d1b")
    description = models.TextField(blank=True)

    class Meta:
        db_table = '"content"."track"'
        ordering = ["name"]

    def __str__(self):
        return f"{self.conference} / {self.name}"
