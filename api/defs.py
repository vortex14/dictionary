from doctest import Example
from time import sleep
from turtle import title
from fastapi import APIRouter, HTTPException, status, Depends
from logger import typhoon_logger
from utils import get_hash
from typing import List
import asyncio
from tortoise.transactions import in_transaction
from models.models_orm import (Definition, Author, DefinitionStatusPy, DefinitionStatusShortFields, DefinitionType, DefinitionsFullRelationFields, Source, SourcePy, Term, DefinitionFullRelationFields, DefinitionShortRelationFields, DefinitionShortRelations,
                               DefinitionFullFields, DefinitionFullFields, AuthorPy, DefinitionSource, DefinitionStatus
                               )

LOG = typhoon_logger(name="api-defs", component="api", level="DEBUG")

router = APIRouter(prefix='/defs', tags=["defintions"])


@router.post("/status", status_code=status.HTTP_200_OK, response_model=DefinitionStatusPy)
async def post_def_status(statusDef: DefinitionStatusShortFields):
    s = await DefinitionStatus.filter(title=statusDef.title).first()
    if isinstance(s, DefinitionStatus):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Definition Status already exist")
    s = DefinitionStatus(title=statusDef.title)
    await s.save()
    return s

@router.delete("/status/{status_id}", status_code=status.HTTP_200_OK, response_model=DefinitionStatusPy)
async def delete_def_status(status_id: int):
    await DefinitionStatus.filter(id=status_id).delete()   

@router.get("/status", status_code=status.HTTP_200_OK, response_model=List[DefinitionStatusPy])
async def def_status():
    return await DefinitionStatus.filter().all()


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[DefinitionFullFields])
async def get_defs(term: str):
    _term = await Term.filter(title=term.strip().lower()).first()
    if not _term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await Definition.filter(term=_term)

@router.get("/relations", status_code=status.HTTP_200_OK, response_model=DefinitionsFullRelationFields)
async def get_full_relations_defs(term: str, source_id: int = None):
    _term = await Term.filter(title=term.strip().lower()).first()
    if not _term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    _defs = []
    
    if source_id:
        _source = await Source.filter(id=source_id).first()
        for _def in await Definition.filter(term=_term, sources=_source):
            _defs.append(DefinitionFullRelationFields(sources=await _def.sources, authors=await _def.authors, definition=_def, status=await _def.status))
    else:
        for _def in await Definition.filter(term=_term):
            _defs.append(DefinitionFullRelationFields(sources=await _def.sources, authors=await _def.authors, definition=_def, status=await _def.status))

    

    return DefinitionsFullRelationFields(definitions=_defs, term=_term)

@router.post("/{def_id}/authors", status_code=status.HTTP_200_OK)
async def add_authors_def(def_id: int, authors: List[int]):
    exist = await Definition.filter(id=def_id).first()
    if not exist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")

    exist_authors = set(_author.id for _author in await exist.authors.all())

    diff = set(authors) - exist_authors
    LOG.info("authors", details={"ids": exist_authors, "diff": list(diff)})
    
    _authors = []
    if len(diff) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found a new authors")
    elif len(diff) > 0:
        for author_id in authors:
            _author = await Author.filter(id=author_id).first()
            if not _author: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Author_id: {author_id} not found")
            _authors.append(_author)

        for _author in _authors: await exist.authors.add(_author)
    return {
        "status": True
    }

@router.post("/{def_id}/sources", status_code=status.HTTP_200_OK)
async def add_sources_def(def_id: int, source: DefinitionSource):
    exist = await Definition.filter(id=def_id).first()
    if not exist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")

    LOG.info("add a new source", details={"id": source.source_id})
    
    _source = await Source.filter(id=source.source_id).first()
    if not _source: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source_id: {source.source_id} not found")
    await exist.sources.clear()
    await exist.sources.add(_source)

    return {
        "status": True
    }

@router.get("/{def_id}/authors", status_code=status.HTTP_200_OK, response_model=List[AuthorPy])
async def get_defs_by_id(def_id: int):
    _def = await Definition.filter(id=def_id).first()
    if not _def: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return [it for it in await _def.authors]    

@router.get("/{def_id}/sources", status_code=status.HTTP_200_OK, response_model=List[SourcePy])
async def get_sources_by_id(def_id: int):
    _def = await Definition.filter(id=def_id).first()
    if not _def: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return [it for it in await _def.sources]  

@router.get("/{def_id}", status_code=status.HTTP_200_OK)
async def get_defs_by_id(def_id: int):
    _def = await Definition.filter(id=def_id).first()
    if not _def:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _def

@router.patch("/{def_id}", status_code=status.HTTP_200_OK, response_model=DefinitionFullRelationFields)
async def update_def_by_id(def_id, definition: DefinitionShortRelationFields):
    _def = await Definition.filter(id=def_id).first()
    _term = None
    _source = None
    payload = {}

    if not _def:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")
    
    if  definition.term:
        _term = await Term.filter(title=definition.term.title).first()
        if not _term: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    
    if definition.content:
        payload["content"] = definition.content
        payload["hash_data"] = get_hash(definition.content.lower())
    
    if _term:
        payload["term"] = _term
    
    if definition.sources:
        _s = await Source.filter(id=definition.sources[0].id).first()
        if not _s: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        await _def.sources.clear()
        await _def.sources.add(_s)

    if payload:
        await Definition.filter(id=def_id).update(**payload)
    
    _term = await _def.term

    return DefinitionFullRelationFields(definition=_def, term=_term)


class ConcurrentLocker:
    _instance = None
    lock = None
    
    def __new__(cls, *args, **kwargs):
        if not ConcurrentLocker._instance:
            ConcurrentLocker.lock = asyncio.Lock()
            ConcurrentLocker._instance = super(ConcurrentLocker, \
               cls).__new__(cls, *args, **kwargs)
        return ConcurrentLocker._instance

    def is_locked(self) -> bool:
        return ConcurrentLocker.lock.locked()

async def locker() -> ConcurrentLocker:
    try:
        c = ConcurrentLocker()
        while c.is_locked():
            await asyncio.sleep(0)
        yield c
    except Exception as e:
        pass





@router.post("/", status_code=status.HTTP_200_OK)
async def post_def(definition: DefinitionShortRelations, locker: ConcurrentLocker = Depends(locker)):

    async with locker.lock:
        _sources = []
        _authors = []

        statusDef = await DefinitionStatus.filter(title=definition.status.title).first()
        if statusDef is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Definition status not found")

        if definition.sources:
            for _s in definition.sources:
                _source = await Source.filter(title=_s.title).first()
            
                if not _source:
                    _source = await Source.create(title=_s.title)
                _sources.append(_source)

        if definition.authors:
            for _a in definition.authors:
                _author = await Author.filter(firt_name=_a.firt_name, last_name=_a.last_name, birth_date=_a.birth_date).first()
                if not _author:
                    _author = await Author.create(firt_name=_a.firt_name, last_name=_a.last_name, birth_date=_a.birth_date, full_name=_a.full_name)
                _authors.append(_author)    

        _term = await Term.filter(title=definition.term.title).first()
        if _term is None: 
            await Term(title=definition.term.title).save()
        
        _hash = get_hash(definition.content.lower())
        
        check_def = await Definition.filter(hash_data=_hash).first()
        if isinstance(check_def, Definition):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Definition already exist")

        new_def = Definition(content=definition.content, hash_data=_hash, term=_term, status=statusDef)
        await new_def.save()
        
        for _source in _sources:
            await new_def.sources.add(_source)


        for _author in _authors:
            await new_def.authors.add(_author)
    
    return DefinitionFullRelationFields(term=_term, definition=new_def, sources=await new_def.sources, authors=await new_def.authors, status=await new_def.status)
    