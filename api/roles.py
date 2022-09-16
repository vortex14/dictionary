from fastapi import APIRouter, HTTPException, status
from logger import typhoon_logger
from utils import get_hash
from typing import List


from models.models_orm import ( Role, RolePy )

LOG = typhoon_logger(name="api-roles", component="api", level="DEBUG")

router = APIRouter(prefix='/roles', tags=["roles"])


@router.get("/", response_model=List[RolePy])
async def roles():
    return await Role.all()

@router.delete("/", status_code=status.HTTP_200_OK)
async def delete_roles(role: RolePy):
    await Role.filter(title=role.title).delete()

@router.put("/", status_code=status.HTTP_200_OK)
async def new_role(role: RolePy):
    roleExist = await Role.exists(title=role.title)
    if roleExist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already created!")
    else:
        await (await Role.create(title=role.title)).save()

