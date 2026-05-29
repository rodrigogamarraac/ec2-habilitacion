from fastapi import FastAPI
from contextlib import asynccontextmanager
from models import *
from api.v1 import table_types
from api.v1 import resevations
from api.v1 import menu
from api.v1 import restaurants
from core import config
from redis.asyncio import Redis
import db.cache as cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.redis_client = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    yield
    await cache.redis_client.close()

app = FastAPI(lifespan=lifespan)

app.include_router(table_types.router,prefix="/api/v1/tables",tags=["table type"])
app.include_router(resevations.router,prefix="/api/v1/reservations",tags=["reservations"])
app.include_router(menu.router,prefix="/api/v1/menus",tags=["menu"])
app.include_router(restaurants.router,prefix="/api/v1/restaurants",tags=["restaurants"])
@app.get("/api/v1/healthz")
async def healthz():
    return {"status": "ok"}
