from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List

from models.models_orm import (Definition, Author, DefinitionType, Term, DefinitionFullRelationFields, DefinitionShortRelationFields, DefinitionShortRelations,
                               DefinitionFullFields, DefinitionFullFields, AuthorPy
                               )

LOG = typhoon_logger(name="api-defs", component="api", level="DEBUG")

router = APIRouter(prefix='/defs', tags=["defintions"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[DefinitionFullFields])
async def get_defs(term: str):
    _term = await Term.filter(title=term.strip().lower()).first()
    if not _term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await Definition.filter(term=_term)

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

@router.get("/{def_id}/authors", status_code=status.HTTP_200_OK, response_model=List[AuthorPy])
async def get_defs_by_id(def_id: int):
    _def = await Definition.filter(id=def_id).first()
    if not _def: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return [it for it in await _def.authors]    
    
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
    _type = None
    payload = {}

    if not _def:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Definition not found")
    
    if  definition.term:
        _term = await Term.filter(title=definition.term.title).first()
        if not _term: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")

    if definition.type:
        _type = await DefinitionType.filter(title=definition.type.title).first()
        if not _type: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type not found")
    
    if definition.content:
        payload["content"] = definition.content
        payload["hash_data"] = get_hash(definition.content.lower())

    if _type:
        payload["type"] = _type
    
    if _term:
        payload["term"] = _term

    if payload:
        await Definition.filter(id=def_id).update(**payload)
    
    _type = await _def.type
    _term = await _def.term

    return DefinitionFullRelationFields(definition=_def, type=_type, term=_term)

@router.post("/", status_code=status.HTTP_200_OK, response_model=DefinitionFullRelationFields)
async def post_def(definition: DefinitionShortRelations):
    _term = await Term.filter(title=definition.term.title).first()
    if not _term: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Term not found")
    _type = await DefinitionType.filter(title=definition.type.title).first()
    if not _type: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Type not found")
    _hash = get_hash(definition.content.lower())
    check_def = await Definition.filter(hash_data=_hash).first()
    if check_def:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Definition already exist")

    new_def = Definition(content=definition.content, hash_data=_hash, type=_type, term=_term)
    await new_def.save()
    return DefinitionFullRelationFields(term=_term, type=_type, definition=new_def)

    