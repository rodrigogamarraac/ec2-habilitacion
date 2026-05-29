from sqlmodel import Field,Relationship
import uuid
from typing import Optional
from models.timeStampModel import TimeStampModel
from datetime import datetime

class Reservation(TimeStampModel,table=True):
    __tablename__="reservation"
    __table_args__ = {"schema": "content"}

    id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    status:str
    starts_at:str
    ends_at:datetime
    restaurant_id:uuid.UUID=Field(foreign_key="content.restaurant.id")
    restaurant: Optional["Restaurant"] = Relationship(back_populates="reservations")
    table_type_id:uuid.UUID=Field(foreign_key="content.table_type.id")
    table_type:Optional["TableType"]=Relationship(back_populates="reservations")
    reservation_guests:list["ReservationGuest"]=Relationship(back_populates="reservation")
