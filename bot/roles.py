from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from models.models_orm import Role

class Form(StatesGroup):
    sub_role_command = State()
    remove_role_name = State()
    role_name = State()



class CommandRoles:
    
    def __init__(self, bot, dp: Dispatcher ,log) -> None:
        self.LOG = log
        self.bot = bot

        self.valid_commands = {
            "Count": self.on_count,
            "Add": self.on_add,
            "Remove": self.on_remove,
            "List": self.on_list
        }
             
        dp.register_message_handler(self.on_new_role, state=Form.role_name)
        dp.register_message_handler(self.on_remove_role, state=Form.remove_role_name)
        dp.register_message_handler(self.subcommand, lambda message: message.text in list(self.valid_commands), state=Form.sub_role_command)
        dp.register_message_handler(self.invalid_subcommand, lambda message: message.text not in list(self.valid_commands), state=Form.sub_role_command)

    
    async def run(self, message: types.Message):
        self.LOG.info("run", details={"command": "/roles"})

        await Form.sub_role_command.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(*self.valid_commands)

        await message.reply("next subcommand", reply_markup=markup)


    async def invalid_subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info("subcommand process roles ...")
        await state.finish()
        await message.reply('debil role', reply_markup=types.ReplyKeyboardRemove())
    
    
    async def subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"subcommand process {message.text}...")
        cmd = self.valid_commands[message.text]
        await cmd(message, state)
    
    async def on_add(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        await Form.role_name.set()

        await message.answer("?")
        
    async def on_new_role(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"create a new role: {message.text}")

        roleExist = await Role.exists(title=message.text)

        match roleExist:
            case True:
                await self.close(message, "Такая роль существует", state)
            case False:
                await (await Role.create(title=message.text)).save()
                await self.close(message, "ok", state)
    
    async def on_count(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        roles = await Role.all()

        await self.close(message, str(len(roles)), state)
    
    
    async def on_list(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        roles = await Role.all()

        _list = ""

        for r in roles: _list += r.title + "\n"

        await self.close(message, _list, state)

    async def on_remove(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        await Form.remove_role_name.set()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        roles = [ r.title for r in await Role.all() ]
        
        markup.add(*roles)

        await message.reply("select", reply_markup=markup)

        # await self.close(message, "done", state)

    async def on_remove_role(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"remove role: {message.text} ...")

        await Role.filter(title=message.text).delete()

        await self.close(message, "removed", state)
    
    async def close(self, message: types.Message, answer: str, state: FSMContext):
        self.LOG.info(f"close {message.text} ...")
        await state.finish()
        await message.answer(answer, reply_markup=types.ReplyKeyboardRemove())