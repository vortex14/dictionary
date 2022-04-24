import os
from nis import match
from typing import List
from bot import KosmoBot
from turtle import title
from unittest import case
from tortoise import Tortoise
from logger import typhoon_logger
from models import ADMIN, UNKNOWN
from fastapi_utils.cbv import cbv
from models.models_orm import Role, User, RolePy
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Depends, FastAPI, status, HTTPException

app = FastAPI()
bot = KosmoBot()
router = InferringRouter()
LOG = typhoon_logger(name="Server", component="api", level="DEBUG")

@cbv(router)
class MainServer:


    @staticmethod
    async def init_base_role():

        for role in (ADMIN, UNKNOWN, ):
            if not (await Role.filter(title=role).count()):
                unknown = await Role.create(title=role)
                await unknown.save()
        
    @app.on_event("startup")
    async def on_startup():
        LOG.info("starting server ...")

        
        await Tortoise.init(
            db_url=os.environ["DB_URL"],
            modules={'models': ['models.models_orm']}
        )
        
       

        await Tortoise.generate_schemas()
        await MainServer.init_base_role()

        await bot.run()


    @router.get("/roles", response_model=List[RolePy])
    async def roles(self):
        return await Role.all()

    @router.delete("/roles", status_code=status.HTTP_200_OK)
    async def delete_roles(self, role: RolePy):
        await Role.filter(title=role.title).delete()
    
    @router.put("/roles", status_code=status.HTTP_200_OK)
    async def new_role(self, role: RolePy):
        roleExist = await Role.exists(title=role.title)
        match roleExist:
            case True:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already created!")
            case False:
                await (await Role.create(title=role.title)).save()
    

    @app.on_event("shutdown")
    async def on_shutdown():
        await bot.close()

app.include_router(router)
