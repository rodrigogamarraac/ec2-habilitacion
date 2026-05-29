from fastapi import APIRouter, Depends, Query
from datetime import date, time
from services.getAvailability import GetAvailability, get_availability_service,AvailabilitySlot

router = APIRouter()

@router.get("/availability/", response_model=list[AvailabilitySlot])
async def get_availability(
    date: date = Query(..., description="2026-06-10"),
    time: time | None= Query(None, description="19:00:00"),
    party: int = Query(..., ge=1, description="Número de personas"),
    table_type: str | None = Query(None, description="Filtro por tipo: intimate, shared"),
    tz: str = Query("UTC", description="Timezone del cliente: America/La_Paz"),
    service: GetAvailability = Depends(get_availability_service)
):
    return await service.get_availability(date, time, party, table_type, timezone)
