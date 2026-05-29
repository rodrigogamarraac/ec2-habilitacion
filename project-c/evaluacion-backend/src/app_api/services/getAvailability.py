from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import Depends
from datetime import date, time, datetime, timedelta
from redis.asyncio import Redis
from zoneinfo import ZoneInfo
import json
import logging
import uuid

from models.table_type import TableType
from models.reservation import Reservation

from db.postgres import get_db
from db.cache import get_redis

from pydantic import BaseModel


logger = logging.getLogger(__name__)

CACHE_TTL = 60
RESERVATION_DURATION = timedelta(minutes=30)


class AvailabilitySlot(BaseModel):

    time: datetime

    table_type: str
    table_type_name: str

    seats: int
    available_seats: int

    price_per_seat: float

class GetAvailability:

    def __init__(
        self,
        db: AsyncSession,
        redis: Redis
    ):
        self.db = db
        self.redis = redis

    def _cache_key(
        self,
        date: date,
        time: time,
        party: int,
        table_type: str | None,
        tz: str
    ) -> str:

        return (
            f"availability:"
            f"{date}:"
            f"{time}:"
            f"{party}:"
            f"{table_type or 'any'}:"
            f"{tz}"
        )

    async def _get_from_cache(
        self,
        key: str
    ) -> list[AvailabilitySlot] | None:

        try:

            cached = await self.redis.get(key)

            if cached:

                data = json.loads(cached)

                return [
                    AvailabilitySlot(**item)
                    for item in data
                ]

        except Exception as e:
            logger.warning(f"Redis get availability fallo: {e}")

        return None

    async def _set_cache(
        self,
        key: str,
        data: list[AvailabilitySlot]
    ) -> None:

        try:

            serialized = json.dumps(
                [
                    item.model_dump(mode="json")
                    for item in data
                ]
            )

            await self.redis.setex(
                key,
                CACHE_TTL,
                serialized
            )

        except Exception as e:
            logger.warning(f"Redis set availability fallo: {e}")

    async def get_availability(
        self,
        date: date,
        time: time,
        party: int,
        table_type: str | None,
        tz: str
    ) -> list[AvailabilitySlot]:

        key = self._cache_key(
            date,
            time,
            party,
            table_type,
            tz
        )

        cached = await self._get_from_cache(key)

        if cached is not None:
            return cached

        result = await self._get_from_db(
            date,
            time,
            party,
            table_type,
            tz
        )

        await self._set_cache(key, result)

        return result

    async def _get_from_db(
        self,
        date: date,
        time: time | None,
        party: int,
        table_type: str | None,
        tz: str
    ) -> list[AvailabilitySlot]:

        try:
            client_tz = ZoneInfo(tz)

        except Exception:
            client_tz = ZoneInfo("UTC")

        reference_time = time or datetime.min.time()

        local_starts_at = datetime.combine(
            date,
            reference_time
        ).replace(tzinfo=client_tz)

        starts_at_utc = (
            local_starts_at
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )

        ends_at_utc = starts_at_utc + RESERVATION_DURATION

        stmt = select(TableType).where(TableType.capacity >= party)

        if table_type and table_type.lower() not in ("", "any"):
            stmt = stmt.where(TableType.id == uuid.UUID(table_type))

        result = await self.db.execute(stmt)
        table_types = result.scalars().all()

        return [
            AvailabilitySlot(
                time=starts_at_utc,
                table_type=tt.type,
                table_type_name=tt.name,
                seats=tt.capacity,
                available_seats=tt.capacity,
                price_per_seat=tt.price
            )
            for tt in table_types
        ]


def get_availability_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):

    return GetAvailability(db, redis)
