from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List


from models.models_orm import ( DefinitionType, DefinitionTypeShortFields, DefinitionTypeFullFields )

LOG = typhoon_logger(name="api-types", component="api", level="DEBUG")

router = APIRouter(prefix='/types', tags=["types"])

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[DefinitionTypeFullFields])
async def get_types():
    return await DefinitionType.all()

@router.delete("/{type_id}", status_code=status.HTTP_200_OK)
async def delete_type(type_id: int):
    return await DefinitionType.filter(type_id=type_id).delete()

@router.post("/", status_code=status.HTTP_200_OK, response_model=DefinitionTypeFullFields)
async def new_type(defType: DefinitionTypeShortFields):
    exist = await DefinitionType.filter(title=defType.title).first()
    if exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Type already exist")
    _def = DefinitionType(title=defType.title)
    await _def.save()
    return _def