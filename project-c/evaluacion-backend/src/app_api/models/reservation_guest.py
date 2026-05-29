from sqlmodel import Field,Relationship
import uuid
from typing import Optional
from models.timeStampModel import TimeStampModel

class ReservationGuest(TimeStampModel,table=True):
    __tablename__="reservation_guest"
    __table_args__ = {"schema": "content"}

    id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    full_name:str
    email:str
    phone:str
    reservation_id:uuid.UUID=Field(foreign_key="content.reservation.id") 
    reservation: Optional["Reservation"] = Relationship(back_populates="reservation_guests")   

