import os
import logging
import asyncio
from logger import typhoon_logger
from aiogram import Bot, Dispatcher, executor, types

class KosmoBot:

    # Initialize bot and dispatcher
    def __init__(self) -> None:
        
        self.LOG = typhoon_logger(name=self.__class__.__name__, component="bot", level="DEBUG")
        self.LOG.info("init bot")
        
        self.bot = Bot(token=os.environ["API_TELEGRAM_BOT_TOKEN"])
        self.dp = Dispatcher(self.bot)
        self.dp.register_message_handler(self.on_message)

    async def on_message(self, message: types.Message):
        self.LOG.info("on new message", details={"command": message.get_command()})

        print(message.get_command())
        
        await message.answer(message.text)

    async def echo(message: types.Message):

        await message.answer(message.text)



    async def close(self):
        await self.bot.session.close()

    async def run(self):
        asyncio.create_task(self.dp.start_polling())
