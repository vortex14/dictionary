from aiogram import Bot, Dispatcher, types
from bot.command import CommandMixin
from models import User, Role


class CommandStart(CommandMixin):
    
    def __init__(self, bot, dp: Dispatcher ,log) -> None:
        self.LOG = log
        self.bot = bot


    async def run(self, user: User, role: Role, message: types.Message):
        self.LOG.info("run", details={"command": "/users", "user": user.first_name, "id": user.telegram_id, "role": role.title})

        await message.answer("Welcome!")

