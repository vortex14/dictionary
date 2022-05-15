from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List


from models.models_orm import ( SourcePy, Source, SourceShortFields, SourceType, SourceTypeShortFields, SourceTypePy, SoureFullRelationFields )

LOG = typhoon_logger(name="api-sources", component="api", level="DEBUG")

router = APIRouter(prefix='/sources', tags=["sources"])    
    
@router.get("/", response_model=List[SourcePy])
async def get_sources():
    return await Source.all()

@router.get("/types", response_model=List[SourceTypePy])
async def get_types():
    return await SourceType.all()



# @router.post("/{source_id}/links")
# async def add_new_link(link: SourceLinkShortFields):
#     exist = await SourceLink.filter(link=link.link)
#     if exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Link already exist")
#     await SourceLink.create(link=link.link)
#     return {
#         "status": True
#     }

@router.post("/types", response_model=SourceTypePy)
async def add_type(stype: SourceTypeShortFields):
    _type = await SourceType.filter(name=stype.name).first()
    if _type: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Type already exist")
    return await SourceType.create(**dict(stype))


@router.post("/{source_id}/types")
async def add_type_source(source_id: int, type_id: int):
    _source = await Source.filter(id=source_id).first()
    if not _source: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not found source")
    
    _type = await SourceType.filter(id=type_id).first()
    if not _type: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not found type")

    await Source.filter(id=source_id).update(type=_type)

    return {
        "status": True
    }

@router.get("/{source_id}/types", response_model=SourceTypePy)
async def get_type_source(source_id: int):
    _source = await Source.filter(id=source_id).first()
    if not _source: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not found source")
    _type = await _source.type
    return _type

@router.get("/{source_id}", response_model=SoureFullRelationFields)
async def get_source_relation(source_id: int):
    _source = await Source.filter(id=source_id).first()
    if not _source: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not found source")
    _type = await _source.type
    return SoureFullRelationFields(type=_type, source=_source)

@router.post("/", response_model=SourcePy)
async def new_source(source: SourceShortFields):
    LOG.info("create a new source", details=dict(source))
    exist = await Source.filter(title=source.title).first()
    if exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT)
    await Source.create(title=source.title)
    return await Source.filter(title=source.title).first() 

@router.patch("/{source_id}", response_model=SourcePy)
async def update_source(source_id: int, source: SourceShortFields):
    LOG.info(f"Update exist source: {source_id}", details=dict(source))
    exist = await Source.filter(id=source_id).first()
    if not exist: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    dup_exist = await Source.filter(title=source.title).first()
    if dup_exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already Exists")
    await Source.filter(id=source_id).update(title=source.title)
    return await Source.filter(title=source.title).first() 
    
  