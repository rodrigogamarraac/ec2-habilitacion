from sqlmodel import Field,Relationship
import uuid
from typing import Optional
from models.timeStampModel import TimeStampModel


class TableType(TimeStampModel,table=True):
    __tablename__="table_type"
    __table_args__ = {"schema": "content"}

    id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    name:str
    type:str
    capacity:float
    description:str
    price:float
    restaurant_id:uuid.UUID=Field(foreign_key="content.restaurant.id")
    restaurant: Optional["Restaurant"] = Relationship(back_populates="table_types")
    reservations:list["Reservation"]=Relationship(back_populates="table_type")
