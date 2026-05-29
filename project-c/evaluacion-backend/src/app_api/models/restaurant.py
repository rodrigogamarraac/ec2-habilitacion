from sqlmodel import Field,Relationship
import uuid
from models.timeStampModel import TimeStampModel


class Restaurant(TimeStampModel,table=True):
    __tablename__="restaurant"
    __table_args__ = {"schema": "content"}
    id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    name:str
    description:str
    address:str
    table_types:list["TableType"]=Relationship(back_populates="restaurant")
    menu:list["Menu"]=Relationship(back_populates="restaurant")
    reservations:list["Reservation"]=Relationship(back_populates="restaurant")
    