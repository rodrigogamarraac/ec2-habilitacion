from fastapi import APIRouter, Depends, Query
from datetime import date
from services.getMenu import GetMenu, get_menu_service,MenuItemResponse

router = APIRouter()

@router.get("/", response_model=list[MenuItemResponse])
async def get_menu(
    date: date = Query(..., description="2026-06-10"),
    service: GetMenu = Depends(get_menu_service)
):
    return await service.get_by_date(date)

