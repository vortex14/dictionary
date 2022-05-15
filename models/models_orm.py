
from unicodedata import name
from pydantic import (BaseModel,BaseSettings, Extra, Field)
from sqlalchemy import null
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise import fields
from tortoise.models import Model
from pydoc import describe
from operator import index
from typing import Tuple
from enum import unique
from copy import deepcopy
from pydantic.dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Optional, Any, Union, Set, List, Dict

class DefinitionType(Model):
    type_id = fields.IntField(pk=True, unique=True)
    title = fields.CharField(max_length=300, unique=True, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)


class Definition(Model):
    id = fields.IntField(pk=True, unique=True)
    type = fields.ForeignKeyField("models.DefinitionType", related_name="type", null=True)
    term = fields.ForeignKeyField("models.Term", related_name="term", null=True)    
    authors: fields.ManyToManyRelation["Author"] = fields.ManyToManyField(
        "models.Author", related_name="author", through="authors_definition", null=True
    )

    sources: fields.ManyToManyRelation["Source"] = fields.ManyToManyField(
        "models.Source", related_name="source", through="sources_definition", null=True
    )

    hash_data = fields.CharField(max_length=200, index=True)

    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)


# Source ----
class Source(Model):
    id = fields.IntField(pk=True, unique=True)
    title = fields.CharField(max_length=250, index=True, unique=True)
    definitions: fields.ManyToManyRelation[Definition]
    type = fields.ForeignKeyField("models.SourceType", related_name="type", null=True)
    links: fields.ManyToManyRelation["SourceLink"] = fields.ManyToManyField(
        "models.SourceLink", related_name="links", through="links_sources", null=True
    )
    created_at = fields.DatetimeField(auto_now_add=True)

class SourceType(Model):
    id = fields.IntField(pk=True, unique=True)
    name = fields.CharField(max_length=250, unique=True) #photo, video, magazine, blog post
    created_at = fields.DatetimeField(auto_now_add=True)

class LinkType(Model):
    id = fields.IntField(pk=True, unique=True)
    title = fields.CharField(max_length=250, unique=True) #photo, video, magazine, blog post
    created_at = fields.DatetimeField(auto_now_add=True)


class SourceLink(Model):
    id = fields.IntField(pk=True, unique=True)
    link = fields.CharField(max_length=250, unique=True)
    type = fields.ForeignKeyField("models.LinkType", related_name="type", null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

SourcePy = pydantic_model_creator(Source)
SourceTypePy = pydantic_model_creator(SourceType)
SourceTypeShortFields = pydantic_model_creator(SourceType, name="SourceTypeShortFields", exclude=('id', 'created_at'))
SourceShortFields = pydantic_model_creator(Source, exclude=('id', 'definitions', 'created_at'), name="SourceShortFields")

SourceLinkPy = pydantic_model_creator(SourceLink)
SourceLinkShortFields = pydantic_model_creator(SourceLink, exclude=('id', 'created_at'), name="SourceLinkShortFields")

LinkTypePy = pydantic_model_creator(LinkType)
LinkTypeShortFields = pydantic_model_creator(LinkType, exclude=('id', 'created_at'), name="LinkTypeShortFields")

class LinkFullRelationFields(BaseModel):
    class Config:
        title = "LinkFullRelationFields"

    link: SourceLinkPy
    type: LinkTypePy = None

class SoureFullRelationFields(BaseModel):
    class Config:
        title = "SoureFullRelationFields"

    source: SourcePy
    type: SourceTypePy = None
# -----


# Author
class Author(Model):
    id = fields.IntField(pk=True, unique=True)
    birth_date = fields.DateField(null=True)
    firt_name = fields.CharField(max_length=100, index=True)
    last_name = fields.CharField(max_length=100, index=True)
    full_name = fields.CharField(max_length=100, index=True, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    definitions: fields.ManyToManyRelation[Definition]
    
AuthorPy = pydantic_model_creator(Author)
AuthorShortFields = pydantic_model_creator(Author, exclude=('id', 'definitions', 'created_at'), name="AuthorShortFields")
# --------

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
RolePy = pydantic_model_creator(Role, exclude=('role_id', ))

TermShortFields = pydantic_model_creator(Term, exclude=('term_id', 'created_at'), name="TermShortFields")
TermFullFields = pydantic_model_creator(Term)

DefinitionShortFields = pydantic_model_creator(Definition, exclude=('id', 'created_at', 'hash_data'), name="DefinitionShortFields")
DefinitionFullFields = pydantic_model_creator(Definition, name="DefinitionFullFields")

DefinitionTypeFullFields = pydantic_model_creator(DefinitionType)
DefinitionTypeShortFields = pydantic_model_creator(DefinitionType, exclude=('id', 'hash_data', 'created_at'), exclude_readonly=True, name="DefinitionTypeShortFields")

class DefinitionShortRelations(DefinitionShortFields):
    class Config:
        title = "DefinitionShortRelations"

    term: TermShortFields
    type: DefinitionTypeShortFields


class DefinitionFullRelationFields(BaseModel):
    class Config:
        title = "DefinitionFullRelations"

    term: TermFullFields = None
    type: DefinitionTypeFullFields = None
    definition: DefinitionFullFields = None

class DefinitionShortRelationFields(DefinitionShortFields):
    class Config:
        title = "DefinitionShortRelationFields"
    
    content: str = None    
    term: TermShortFields = None
    type: DefinitionTypeShortFields = None

async def get_user(source_user: dict) -> Tuple[Role, User]:
    last_name = source_user["last_name"]
    first_name = source_user["first_name"]
    username = source_user["username"]

    this = await User.filter(telegram_id=source_user["id"]).first()
    
    if this: return (await this.role), this

    role = await Role.filter(title=UNKNOWN).first()
    user = User(

        telegram_id=source_user["id"],
        username=username,
        last_name=last_name,

        first_name=first_name,
        language_code=source_user["language_code"],

        role=role
    )
    await user.save()
    return role, user