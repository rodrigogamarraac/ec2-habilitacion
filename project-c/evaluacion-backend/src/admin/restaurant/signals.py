from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import redis
import os

r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))

from .models import TableType, MenuItem, Menu, Reservation

@receiver([post_save, post_delete], sender=TableType)
def invalidate_table_types(sender, **kwargs):
    r.delete("table_types:all")

@receiver([post_save, post_delete], sender=MenuItem)
@receiver([post_save, post_delete], sender=Menu)
def invalidate_menu(sender, **kwargs):
    for key in r.scan_iter("menu:*"):
        r.delete(key)

@receiver([post_save, post_delete], sender=Reservation)
def invalidate_availability(sender, **kwargs):
    for key in r.scan_iter("availability:*"):
        r.delete(key)