from django.db import models
from .base import Base
from .session import Session

class Registration(Base):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        WAITLIST = "waitlist", "Waitlist"
        CANCELLED = "cancelled", "Cancelled"

    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="registrations"
    )
    user_email = models.EmailField(max_length=254)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CONFIRMED
    )

    class Meta:
        db_table = '"content"."registration"'
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["session", "status"], name="reg_session_status_idx"),
        ]

    def __str__(self):
        return f"{self.user_email} @ {self.session} [{self.status}]"
