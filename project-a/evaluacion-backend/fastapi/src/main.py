import logging
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from src.api.v1 import sessions, tracks, health

logging.basicConfig(
    level=logging.INFO,
    format="time=%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
)

app = FastAPI(
    title="Conference API",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

app.include_router(sessions.router, prefix="/api/v1")
app.include_router(tracks.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
