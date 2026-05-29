from sqlmodel import Field,Relationship
import uuid
from typing import Optional
from models.timeStampModel import TimeStampModel

class MenuItem(TimeStampModel,table=True):
    __tablename__="menu_item"
    __table_args__ = {"schema": "content"}

    id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    name:str
    description:str
    course_number:int
    ingredients:str
    price:float

    menu_id:uuid.UUID=Field(foreign_key="content.menus.id")
    menu: Optional["Menu"] = Relationship(back_populates="menu_items")
