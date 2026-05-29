from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
import json
import logging
from models.table_type import TableType
from redis.asyncio import Redis
from db.postgres import get_db
from db.cache import get_redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)
import uuid

CACHE_KEY = "table_types:all"
CACHE_TTL = 300  

class TableTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    seats: int
    description: str

    class Config:
        from_attributes = True
        
class GetAllTableTypes:
    def __init__(self, db: AsyncSession,redis:Redis):
        self.db = db
        self.redis=redis
        
    async def _get_from_cache(self) -> list[TableTypeResponse] | None:
        try:
            cached = await self.redis.get(CACHE_KEY)
            if cached:
                data = json.loads(cached)
                return [TableTypeResponse(**item) for item in data]
        except Exception as e:
            logger.warning(f"Redis get tables fallo: {e}")
        return None
    
    async def _set_cache(self, data: list[TableTypeResponse]) -> None:
        try:
            serialized = json.dumps([item.model_dump(mode="json") for item in data])
            await self.redis.setex(CACHE_KEY, CACHE_TTL, serialized)
        except Exception as e:
            logger.warning(f"Redis set tables fallo: {e}")
            
    async def get_all(self) -> list[TableTypeResponse]:
        cached = await self._get_from_cache()
        if cached is not None:
            return cached
        
        result = await self.db.execute(select(TableType))
        table_types = result.scalars().all()
        response = [
            TableTypeResponse(
                id=tt.id,
                name=tt.name,
                seats=tt.capacity,
                description=tt.description
            )
            for tt in table_types
        ]

        await self._set_cache(response)

        return response
        

def get_all_table_types(db: AsyncSession = Depends(get_db),redis:Redis=Depends(get_redis)):
    return GetAllTableTypes(db,redis)