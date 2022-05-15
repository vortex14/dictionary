from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List


from models.models_orm import (Author, DefinitionType, Role, Term, User, RolePy, DefinitionFullRelationFields, TermShortFields, TermFullFields, DefinitionFullFields, 
                               DefinitionShortFields, DefinitionTypeShortFields, DefinitionTypeFullFields, TermFullFields, DefinitionFullFields, DefinitionShortRelationFields, DefinitionShortRelations,
                               SourcePy, Source, SourceShortFields, AuthorPy, AuthorShortFields, Definition
                               )

LOG = typhoon_logger(name="api-sources", component="api", level="DEBUG")

router = APIRouter(prefix='/sources', tags=["sources"])    
    
# source
@router.get("/", response_model=List[SourcePy])
async def get_sources():
    return await Source.all()

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
    
  