from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List

from models.models_orm import ( LinkType, LinkTypePy, LinkTypeShortFields, SourceLink, SourceLinkPy, SourceLinkShortFields, LinkFullRelationFields )

LOG = typhoon_logger(name="api-links", component="api", level="DEBUG")

router = APIRouter(prefix='/links', tags=["links"])


@router.get("/", response_model=List[SourceLinkPy])
async def get_links():
    return await SourceLink.all()

@router.post("/")
async def add_new_link(link: SourceLinkShortFields):
    exist = await SourceLink.filter(link=link.link)
    if exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Link already exist")
    await SourceLink.create(link=link.link)
    return {
        "status": True
    }

@router.get("/{link_id}/", response_model=LinkFullRelationFields)
async def get_link(link_id: int):

    _link = await SourceLink.filter(id=link_id).first()
    if not _link: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    _type = await _link.type
    return LinkFullRelationFields(link=_link, type=_type)

@router.get("/types")
async def get_link_types():
    return await LinkType.all()

@router.post("/types", response_model=LinkTypePy)
async def add_link_type(ltype: LinkTypeShortFields):
    exist = await LinkType.filter(title=ltype.title).first()
    if exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Type already exist")
    await LinkType.create(title=ltype.title)
    return await LinkType.filter(title=ltype.title).first()

@router.post("/{link_id}/types")
async def add_link_type(link_id: int, type_link: LinkTypeShortFields):
    exist = await SourceLink.filter(id=link_id).first()
    if not exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Link doesn't exist")
    
    exits_type = await LinkType.filter(title=type_link.title).first()
    if not exits_type: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Link type doesn't exist")
    await SourceLink.filter(id=link_id).update(type=exits_type) 
    return {
        "status": True
    }