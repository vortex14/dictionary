from pydoc import describe
from tortoise import Tortoise, fields, run_async
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model

class User(Model):

    user_id = fields.IntField(pk=True)
    role_id = fields.ForeignKeyField(
        "models.Role", related_name="role"
    )
    telegram_id = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)

class Role(Model):
    
    role_id = fields.IntField(pk=True)
    title = fields.CharField(max_length=100)

UserPy = pydantic_model_creator(User)
RolePy = pydantic_model_creator(Role, exclude=('role_id',))
