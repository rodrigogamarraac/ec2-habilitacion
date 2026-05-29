from sqlmodel import SQLModel
from datetime import datetime

class TimeStampModel(SQLModel):
    created_at:datetime
    updated_at:datetime
    
    