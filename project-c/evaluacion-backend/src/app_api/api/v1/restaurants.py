from fastapi import APIRouter, Depends, Query
from datetime import date
from services.getMenuFilter import GetMenuFilter,get_menu_service,MenuItemResponse
import uuid

router = APIRouter()

@router.get("/{id}/menu", response_model=list[MenuItemResponse])
async def get_menu_filter_allergens(
    id:uuid.UUID,
    date: date = Query(..., description="2026-06-10"),
    exclude_allergens:str | None = Query(None),
    service:GetMenuFilter = Depends(get_menu_service)
):
    return await service.get_menu_filter_allergens(id,date,exclude_allergens)

@router.get("/")
async def get_restaurants(
    
    service:GetMenuFilter = Depends(get_menu_service)
):
    return await service.get_restaurants()

