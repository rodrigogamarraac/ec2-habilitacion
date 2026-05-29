from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.postgres import get_db_session
from src.db.redis import get_redis

router = APIRouter(tags=["health"])

@router.get("/healthz")
async def healthz(
    db: AsyncSession = Depends(get_db_session),
    redis = Depends(get_redis),
):
    checks: dict[str, str] = {}
    ok = True

    try:
        await db.scalar(select(1))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "error"
        ok = False

    checks["redis"] = "ok" if redis is not None else "unavailable"

    if not ok:
        return JSONResponse(status_code=503, content={"status": "error", "checks": checks})
    
    return {"status": "ok", "checks": checks}
