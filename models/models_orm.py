from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise import Tortoise, fields, run_async
from tortoise.models import Model
from pydoc import describe
from operator import index
from typing import Tuple
from enum import unique

class DefinitionType(Model):
    type_id = fields.IntField(pk=True, unique=True)
    title = fields.CharField(max_length=300, unique=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)

class Definition(Model):
    id = fields.IntField(pk=True, unique=True)
    type = fields.ForeignKeyField("models.DefinitionType", related_name="type", null=True)
    
    terms: fields.ManyToManyRelation["Term"] = fields.ManyToManyField(
        "models.Term", related_name="definitions", through="term_definitions"
    )

    hash_data = fields.CharField(max_length=200, index=True)

    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

class Term(Model):
    term_id = fields.IntField(pk=True, unique=True)
    title = fields.CharField(max_length=255, index=True, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    definitions: fields.ManyToManyRelation[Definition]

class User(Model):
    telegram_id = fields.BigIntField(unique=True)

    user_id = fields.IntField(pk=True, unique=True)
    username = fields.CharField(max_length=100, null=True)
    last_name = fields.CharField(max_length=100, null=True)
    first_name = fields.CharField(max_length=100, null=True)
    language_code = fields.CharField(max_length=10)
    created_at = fields.DatetimeField(auto_now_add=True)
    role = fields.ForeignKeyField("models.Role", related_name="role")


UNKNOWN = "unknown"
ADMIN = "admin"

class Role(Model):
    
    role_id = fields.IntField(pk=True)
    title = fields.CharField(max_length=100, unique=True)

UserPy = pydantic_model_creator(User)
RolePy = pydantic_model_creator(Role, exclude=('role_id',))
TermPy = pydantic_model_creator(Term, exclude=('term_id', ))
DefinitionPy = pydantic_model_creator(Definition, exclude=('id', 'hash_data', 'created_at'))



async def get_user(source_user: dict) -> Tuple[Role, User]:
    last_name = source_user["last_name"]
    first_name = source_user["first_name"]
    username = source_user["username"]

    this = await User.filter(telegram_id=source_user["id"]).first()
    
    if this: return (await this.role), this

    role = await Role.filter(title=UNKNOWN).first()

    return role, await User(

        telegram_id=source_user["id"],
        username=username,
        last_name=last_name,

        first_name=first_name,
        language_code=source_user["language_code"],

        role=role
    ).save()