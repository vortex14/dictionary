from pydoc import describe
from tortoise import Tortoise, fields, run_async
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model
from typing import Tuple

class User(Model):
    telegram_id = fields.IntField()

    user_id = fields.IntField(pk=True)
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
    title = fields.CharField(max_length=100)

UserPy = pydantic_model_creator(User)
RolePy = pydantic_model_creator(Role, exclude=('role_id',))


async def get_user(source_user: dict) -> Tuple[Role, User]:
    last_name = source_user["last_name"]
    first_name = source_user["first_name"]
    username = source_user["username"]

    this = await User.filter(telegram_id=source_user["id"]).first()
    
    if this: return (await this.role), this

    role = await Role.filter(title=UNKNOWN).first()
    print(source_user)

   

    return role, await User.create(

        telegram_id=source_user["id"],
        username=username,
        last_name=last_name,

        first_name=first_name,
        language_code=source_user["language_code"],

        role=role
    )