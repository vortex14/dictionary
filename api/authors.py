from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from typing import List


from models.models_orm import ( Author, AuthorPy, AuthorShortFields )

LOG = typhoon_logger(name="api-authors", component="api", level="DEBUG")

router = APIRouter(prefix='/authors', tags=["authors"])

@router.get("/", response_model=List[AuthorPy])
async def get_authors():
    return await Author.all()

@router.post("/", response_model=AuthorPy)
async def create_author(author: AuthorShortFields):
    LOG.info("create a new author", details=dict(author))
    exist = await Author.filter(**dict(author)).first()
    if exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already Exists")
    await Author.create(**dict(author))
    return await Author.filter(**dict(author)).first() 

@router.patch("/{author_id}", response_model=AuthorPy)
async def update_author(author_id: int, author: AuthorShortFields):
    LOG.info(f"Update exist author", details=dict(author) | {"author_id": author_id})
    exist = await Author.filter(id=author_id).first()
    if not exist: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    dup_exist = await Author.filter(**dict(author)).first()
    if dup_exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already Exists")
    await Author.filter(id=author_id).update(**dict(author))
    return await Author.filter(id=author_id).first() 