from email.policy import default
import os
import asyncio
from logger import typhoon_logger
from aiogram import Bot, Dispatcher, executor, types

from models import User, get_user, ADMIN, UNKNOWN

from .definition import CommandDefinition
from .users import CommandUsers
from .roles import CommandRoles
from .start import CommandStart
from .terms import CommandTerms
from .types import CommandDefinitionTypes

from pydantic import BaseModel
from aiogram.dispatcher import FSMContext

from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()

class Form(StatesGroup):
    subcommand = State()

class KosmoBot:

    def __init__(self) -> None:
        
        self.LOG = typhoon_logger(name=self.__class__.__name__, component="bot", level="DEBUG")
        self.LOG.info("init bot")
        
        self.bot = Bot(token=os.environ["API_TELEGRAM_BOT_TOKEN"])
        self.dp = Dispatcher(self.bot, storage=storage)
        self.dp.register_message_handler(self.on_message)

        self.commands = {
            "/start": CommandStart(self.bot, self.dp, self.LOG),
            "/users": CommandUsers(self.bot, self.dp, self.LOG),
            "/roles": CommandRoles(self.bot, self.dp, self.LOG),

            "/terms": CommandTerms(self.bot, self.dp, self.LOG),
            "/def": CommandDefinition(self.bot, self.dp, self.LOG),
            "/types": CommandDefinitionTypes(self.bot, self.dp, self.LOG)
        }

    async def on_cancel(self, message: types.Message):
        await message.answer("canceled", reply_markup=types.ReplyKeyboardRemove() )

    async def on_message(self, message: types.Message):
        command = message.get_command()

        role, user = await get_user(message.from_user)   
        print(role, user)
        self.LOG.info("on new message", details={"user_role": role.title, "command": message.get_command(), "handlers": len(self.dp.message_handlers.handlers), **dict(user) } )
        if self.commands.get(command):
            return await self.commands[command].run(user, role, message)
            
        await self.on_cancel(message)   

    async def close(self):
        bot = self.bot.get_session()
        bot.close()

    async def run(self):
        asyncio.create_task(self.dp.start_polling())
