from cgitb import handler
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext

from devtools import debug

class Form(StatesGroup):
    subcommand = State()


class CommandUsers:
    
    def __init__(self, bot, dp: Dispatcher ,log) -> None:
        self.LOG = log
        self.bot = bot

        self.valid_commands = ("Count", "Add", "enything")
             
        dp.register_message_handler(self.subcommand, lambda message: message.text in self.valid_commands, state=Form.subcommand)
        dp.register_message_handler(self.invalid_subcommand, lambda message: message.text not in self.valid_commands, state=Form.subcommand)

    
    async def run(self, message: types.Message):
        self.LOG.info("run", details={"command": "/users"})

        await Form.subcommand.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(*self.valid_commands)

        await message.reply("next subcommand", reply_markup=markup)


    async def invalid_subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info("subcommand process user ...")

        # current_state = await state.get_state()
        await state.finish()

        await message.reply('debil', reply_markup=types.ReplyKeyboardRemove())
    
    
    async def subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info("subcommand process user ...")

        # current_state = await state.get_state()
        await state.finish()

        await message.reply('ok', reply_markup=types.ReplyKeyboardRemove())

    async def change_status(self):
        pass

    async def create(self):
        pass