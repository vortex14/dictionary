import os
import re
from struct import pack
from typing import List
from bot import KosmoBot, terms
from tortoise import Tortoise
from logger import typhoon_logger
from models import ADMIN, UNKNOWN, Definition
from fastapi_utils.cbv import cbv
from models.models_orm import (DefinitionType, Role, Term, User, RolePy, DefinitionFullRelationFields, TermShortFields, TermFullFields, DefinitionFullFields, 
                               DefinitionShortFields, DefinitionTypeShortFields, DefinitionTypeFullFields, TermFullFields, DefinitionFullFields, DefinitionShortRelationFields, DefinitionShortRelations)
from utils import get_hash
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
                await Role(title=role).save()
        
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

    @router.get("/")
    async def roles():
        return {
            "status": True
        }

    @router.get("/roles", response_model=List[RolePy])
    async def roles(self):
        return await Role.all()

    @router.delete("/roles", status_code=status.HTTP_200_OK)
    async def delete_roles(self, role: RolePy):
        await Role.filter(title=role.title).delete()
    
    @router.get("/terms", status_code=status.HTTP_200_OK, response_model=List[TermFullFields])
    async def get_terms(self):
       return await Term.all()
    
    @router.get("/terms/{term_id}", status_code=status.HTTP_200_OK, response_model=TermFullFields)
    async def get_term_by_id(self, term_id):
       _term = await Term.filter(term_id=term_id).first()
       if not _term: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
       return _term

    @router.patch("/terms/{term_id}", status_code=status.HTTP_200_OK, response_model=TermFullFields)
    async def get_term_by_id(self, term_id, term: TermShortFields):
       _term = await Term.filter(term_id=term_id).first()
       if not _term: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
       await Term.filter(term_id=term_id).update(title=term.title)

       return await Term.filter(term_id=term_id).first()

    @router.get("/defs", status_code=status.HTTP_200_OK, response_model=List[DefinitionFullFields])
    async def get_defs(self, term: str):
        _term = await Term.filter(title=term.strip().lower()).first()
        if not _term:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return await Definition.filter(terms=_term)
    
    @router.get("/defs/{def_id}", status_code=status.HTTP_200_OK)
    async def get_defs_by_id(self, def_id: int):
        _def = await Definition.filter(id=def_id).first()
        if not _def:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return _def

    @router.patch("/defs/{def_id}", status_code=status.HTTP_200_OK, response_model=DefinitionFullRelationFields)
    async def update_def_by_id(self, def_id, definition: DefinitionShortRelationFields):
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

    @router.post("/defs", status_code=status.HTTP_200_OK, response_model=DefinitionFullRelationFields)
    async def post_def(self, definition: DefinitionShortRelations):
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

    @router.put("/roles", status_code=status.HTTP_200_OK)
    async def new_role(self, role: RolePy):
        roleExist = await Role.exists(title=role.title)
        match roleExist:
            case True:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already created!")
            case False:
                await (await Role.create(title=role.title)).save()
    

    @router.get("/types", status_code=status.HTTP_200_OK, response_model=List[DefinitionTypeFullFields])
    async def get_types(self):
        return await DefinitionType.all()
    
    
    @router.delete("/types/{type_id}", status_code=status.HTTP_200_OK)
    async def delete_type(self, type_id: int):
        return await DefinitionType.filter(type_id=type_id).delete()
    
    @router.post("/types", status_code=status.HTTP_200_OK, response_model=DefinitionTypeFullFields)
    async def new_type(self, defType: DefinitionTypeShortFields):
        exist = await DefinitionType.filter(title=defType.title).first()
        if exist: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Type already exist")
        _def = DefinitionType(title=defType.title)
        await _def.save()
        return _def

    @app.on_event("shutdown")
    async def on_shutdown():
        await bot.close()

app.include_router(router)
