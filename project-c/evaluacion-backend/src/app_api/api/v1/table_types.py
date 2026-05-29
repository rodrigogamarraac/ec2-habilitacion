from fastapi import APIRouter,Depends
from services.getAllTableTypes import GetAllTableTypes,get_all_table_types
from services.getAllTableTypes import TableTypeResponse

router = APIRouter()

@router.get("/types", response_model=list[TableTypeResponse])
async def get_all(
    service: GetAllTableTypes = Depends(get_all_table_typess)
):
    tables = await service.get_all()
    return tables
