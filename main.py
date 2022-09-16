import os
import re
from struct import pack
from typing import List
from bot import KosmoBot, terms
from tortoise import Tortoise
from fastapi import APIRouter
from logger import typhoon_logger
from models import ADMIN, UNKNOWN, Definition
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.cbv import cbv
from models.models_orm import (Author, DefinitionType, Role, Term, User, RolePy, DefinitionFullRelationFields, TermShortFields, TermFullFields, DefinitionFullFields, 
                               DefinitionShortFields, DefinitionTypeShortFields, DefinitionTypeFullFields, TermFullFields, DefinitionFullFields, DefinitionShortRelationFields, DefinitionShortRelations,
                               SourcePy, Source, SourceShortFields, AuthorPy, AuthorShortFields
                               )
from utils import get_hash
from fastapi_utils.inferring_router import InferringRouter
from fastapi import Depends, FastAPI, status, HTTPException
from api import author_router, def_router, term_router, type_router, role_router, source_router, link_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = KosmoBot()
router = InferringRouter()

LOG = typhoon_logger(name="Server", component="api", level="DEBUG")

@cbv(router)
class MainServer:
    @staticmethod
    async def init_base_role():
        for role in (ADMIN, UNKNOWN, ):
            if not (await Role.filter(title=role).count()):
                await Role(title=role).save()
        
    @app.get("/")
    def get_base():
        return {
            "status": True
        }
    
    @app.on_event("startup")
    async def on_startup():
        LOG.info("starting server ...")
        # await sleep(6)

        await Tortoise.init(
            db_url=os.environ["DATABASE_URL"],
            modules={'models': ['models.models_orm']}
        )
        try:
            await Tortoise.generate_schemas()
        except Exception as e:
            LOG.error(str(e))

        await MainServer.init_base_role()

        await bot.run()

        LOG.info("Started")

    @app.on_event("shutdown")
    async def on_shutdown():
        await bot.close()

for route in [router, author_router, term_router, def_router, role_router, source_router, link_router]:
    app.include_router(route)