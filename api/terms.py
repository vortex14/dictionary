from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List


from models.models_orm import (Author, DefinitionType, Role, Term, User, RolePy, DefinitionFullRelationFields, TermShortFields, TermFullFields, DefinitionFullFields, 
                               DefinitionShortFields, DefinitionTypeShortFields, DefinitionTypeFullFields, TermFullFields, DefinitionFullFields, DefinitionShortRelationFields, DefinitionShortRelations,
                               SourcePy, Source, SourceShortFields, AuthorPy, AuthorShortFields, Definition
                               )

LOG = typhoon_logger(name="api-terms", component="api", level="DEBUG")

router = APIRouter(prefix='/terms', tags=["terms"])

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[TermFullFields])
async def get_terms():
    return await Term.all()

@router.get("/{term_id}", status_code=status.HTTP_200_OK, response_model=TermFullFields)
async def get_term_by_id(term_id):
    _term = await Term.filter(term_id=term_id).first()
    if not _term: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    return _term

@router.patch("/{term_id}", status_code=status.HTTP_200_OK, response_model=TermFullFields)
async def get_term_by_id(term_id, term: TermShortFields):
    _term = await Term.filter(term_id=term_id).first()
    if not _term: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    await Term.filter(term_id=term_id).update(title=term.title)

    return await Term.filter(term_id=term_id).first()

