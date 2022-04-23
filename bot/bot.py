import os
import logging
import asyncio
from nis import match
from typing_extensions import Self
from logger import typhoon_logger
from aiogram import Bot, Dispatcher, executor, types

from .users import CommandUsers
from .roles import CommandRoles

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
            "/users": CommandUsers(self.bot, self.dp, self.LOG),
            "/roles": CommandRoles(self.bot, self.dp, self.LOG)
        }


    async def on_message(self, message: types.Message):
        command = message.get_command()

        self.LOG.info("on new message", details={ "command": message.get_command(), "handlers": len(self.dp.message_handlers.handlers) } )

        match command:
            case '/users':
                await self.commands[command].run(message)
            case "/roles":
                await self.commands[command].run(message)

    async def close(self):
        bot = self.bot.get_session()
        bot.close()


    async def run(self):
        asyncio.create_task(self.dp.start_polling())
