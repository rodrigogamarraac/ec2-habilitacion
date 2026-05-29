from django.db import models
from .base import Base

class Speaker(Base):
    name = models.CharField(max_length=200)
    affiliation = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = '"content"."speaker"'
        ordering = ["name"]

    def __str__(self):
        return self.name
