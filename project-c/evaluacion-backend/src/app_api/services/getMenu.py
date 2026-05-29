from pydantic import BaseModel
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from datetime import date
from models.menu import Menu
from models.menu_item import MenuItem
from db.postgres import get_db
from db.cache import get_redis
from redis.asyncio import Redis
import json
import logging

logger = logging.getLogger(__name__)
CACHE_TTL=300

class MenuItemResponse(BaseModel):
    id: uuid.UUID
    course: int
    name: str
    description: str
    price: float
    allergens: list[str]

    class Config:
        from_attributes = True


class GetMenu:
    def __init__(self, db: AsyncSession,redis:Redis):
        self.db = db
        self.redis=redis
        
    def _cache_key(self, date: date) -> str:
        return f"menu:{date}"
    
    async def _get_from_cache(self, key: str) -> list[MenuItemResponse] | None:
            try:
                cached = await self.redis.get(key)
                if cached:
                    data = json.loads(cached)
                    return [MenuItemResponse(**item) for item in data]
            except Exception as e:
                logger.warning(f"Redis get menu fallo: {e}")
            return None
        
    async def _set_cache(self, key: str, data: list[MenuItemResponse]) -> None:
        try:
            serialized = json.dumps([item.model_dump(mode="json") for item in data])
            await self.redis.setex(key, CACHE_TTL, serialized)
        except Exception as e:
            logger.warning(f"Redis set menu fallo: {e}")
    
    async def get_by_date(self, date: date) -> list[MenuItemResponse]:
        key = self._cache_key(date)
        
        cached = await self._get_from_cache(key)
        if cached is not None:
            return cached
        
        menu_stmt = select(Menu).where(
            Menu.active_from <= date,
            Menu.active_to >= date
        )
        menu_result = await self.db.execute(menu_stmt)
        menu = menu_result.scalars().first()

        if not menu:
            return []

        items_stmt = select(MenuItem).where(
            MenuItem.menu_id == menu.id
        ).order_by(MenuItem.course_number)

        items_result = await self.db.execute(items_stmt)
        items = items_result.scalars().all()

        response = [
            MenuItemResponse(
                id=item.id,
                course=item.course_number,
                name=item.name,
                description=item.description,
                price=item.price,
                allergens=[a.strip() for a in item.ingredients.split(",") if a.strip()]
            )
            for item in items
        ]
        await self._set_cache(key, response)

        return response
   

def get_menu_service(db: AsyncSession = Depends(get_db),redis:Redis = Depends(get_redis)):
    return GetMenu(db,redis)