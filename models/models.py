import datetime
from pydantic import BaseModel


class User(BaseModel):

    user_id: int
    role_id: int
    telegram_id: int
    created_at: datetime.date


class Role(BaseModel):

    role_id: int
    title: str


class Command(BaseModel):

    command_id: int
    title: str
    active: bool


class Definition(BaseModel):

    created_at: datetime.date
    updated_at: datetime.date
    definition_id: int
    definition_type: int
    term_id: int
    content: str


class DefinitionType(BaseModel):

    defenition_type_id: int
    name: str


class Term(BaseModel):

    term_id: int
    title: str
    created_at: datetime.date
    updated_at: datetime.date


class Menu(BaseModel):

    menu_id: int
    image: bytes
    active: bool
    title: str


class Submenu(BaseModel):

    submenu_id: int
    menu_id: int
    active: bool
    image: bytes


class Message(BaseModel):

    id: int
    title: str
    description: str
