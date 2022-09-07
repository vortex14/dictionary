from operator import iconcat
from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List


from models.models_orm import ( Term, TermShortFields, TermFullFields, TermFullFields )

LOG = typhoon_logger(name="api-terms", component="api", level="DEBUG")

router = APIRouter(prefix='/terms', tags=["terms"])

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[TermFullFields])
async def get_terms(search: str = None):
    if not search:
        return await Term.all()
    else:
        return await Term.filter(title__icontains=search).all()


@router.post("/", status_code=status.HTTP_200_OK, response_model=TermFullFields)
async def post_term(term: TermShortFields):
    _term = await Term.exists(title=term.title)

    match _term:
        case True:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Term already exist!")
        case False:
            term = await Term.create(title=term.title)
            return term

@router.delete("/{term_id}", status_code=status.HTTP_200_OK)
async def delete_term(term_id: int):
    LOG.debug(f"remove term by id: {term_id}")
    await Term.filter(term_id=term_id).delete()

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

