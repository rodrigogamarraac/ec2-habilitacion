from django.db import models
from .base import Base

class Conference(Base):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    timezone = models.CharField(max_length=50, default="UTC")

    class Meta:
        db_table = '"content"."conference"'
        ordering = ["-starts_at"]

    def __str__(self):
        return self.name
