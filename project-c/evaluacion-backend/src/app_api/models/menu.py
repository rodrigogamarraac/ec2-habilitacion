from sqlmodel import Field,Relationship
import uuid
from typing import Optional
from models.timeStampModel import TimeStampModel
from datetime import date

class Menu(TimeStampModel,table=True):
    __tablename__="menu"
    __table_args__ = {"schema": "content"}

    id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    name:str
    description:str
    courses_count:int
    active_from:date
    active_to:date
    restaurant_id:uuid.UUID=Field(foreign_key="content.restaurant.id") 
    restaurant: Optional["Restaurant"] = Relationship(back_populates="menu")   
    menu_items:list["MenuItem"]=Relationship(back_populates="menu")
