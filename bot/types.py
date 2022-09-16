from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
from models import User, Role, DefinitionType
import os
from typing import List


class Form(StatesGroup):
    sub_type_command = State()
    remove_type_name = State()
    type_name = State()
    update_type_name = State()

    sub_detail_type_command = State()

types_cb = CallbackData('post', 'id', 'action')  # post:<id>:<action>

PER_COUNT=int(os.environ["PAGE_DEF_PER_COUNT"])
MAX_SEARCH_OUTPUT=int(os.environ["MAX_SEARCH_OUTPUT"])

class DefinitionTypeMixin:

    @staticmethod
    async def on_cancel(query: types.CallbackQuery, state: FSMContext):
        await state.finish()
        await query.message.delete()
        await query.message.answer("canceled", reply_markup=types.ReplyKeyboardRemove() )
        # await query.message.edit_text("canceled", reply_markup=types.ReplyKeyboardRemove())

    @staticmethod
    async def on_type_edit(message: types.Message, state: FSMContext):
        await Form.update_type_name.set()

        await message.answer("-> ?", reply_markup=types.ReplyKeyboardRemove())

    @staticmethod
    async def update_type_name(message: types.Message, state: FSMContext):
        new_content = message.text.lower()
        typeExist = await DefinitionType.exists(title=new_content)
        current_state = await state.get_data()
        if typeExist:
            await state.finish()
            await message.answer("Такой тип уже есть", reply_markup=types.ReplyKeyboardRemove())
        else:
            await state.finish()
            await DefinitionType.filter(type_id=int(current_state["type_id"])).update(title=new_content)

            await message.answer("Обновлено", reply_markup=types.ReplyKeyboardRemove())



    async def on_select_type(self, query: types.CallbackQuery, state: FSMContext):
        self.LOG.info("select type")
        _type_id = int(query.data.split(":")[1])
        current_state = await state.get_data()
        await state.update_data(type_id=_type_id)
        _type = await DefinitionType.filter(type_id=_type_id).first()
        self.LOG.info("select def type", details={**dict(_type), **dict(current_state)})
        await Form.sub_detail_type_command.set()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        cmds = list(self.types_commands)
        if not current_state.get("def_id"):
            cmds = list(filter(lambda cmd: cmd != "Add", list(self.types_commands)))
            

        markup.add(*cmds)
        

        await query.message.answer(_type.title, reply_markup=markup)

    async def def_first_list(self, message: types.Message, state: FSMContext):
        _types = await DefinitionType.all()
        count = len(_types)
        await state.update_data(page=1, count=count)
        is_next = count > PER_COUNT
        self.LOG.info(f"process {message.text} ...", details={"is_next": is_next})

        await message.reply(f"Добавленные типы: {count}", reply_markup=types.ReplyKeyboardRemove())
        await message.reply(":", reply_markup=self.get_type_list(1, _types, is_next))

    @staticmethod
    async def on_next_types(query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_next = data["count"] > (data["page"] + 1) * PER_COUNT
            next_page = data["page"] + 1
            data.update(page=next_page)
            _types = await DefinitionType.all()
            await query.message.edit_text("->", reply_markup=DefinitionTypeMixin.get_type_list(next_page, _types, is_next))
        
    @staticmethod
    async def on_back_types(query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_back = data["page"] != 1
            next_page = data["page"] - 1
            data.update(page=next_page)
            _types = await DefinitionType.all()
            await query.message.edit_text("<-", reply_markup=DefinitionTypeMixin.get_type_list(next_page, _types, is_back))    

    @staticmethod
    def get_type_list(page:int, def_types: List[DefinitionType], is_next: bool) -> types.InlineKeyboardMarkup:
        """
        Generate keyboard with list of Types
        """

        markup = types.InlineKeyboardMarkup()
        skip = 0

        if page != 1: skip = (page - 1) * PER_COUNT

        for _type in def_types[skip: skip + PER_COUNT]:
            markup.add(
                types.InlineKeyboardButton(
                    f"{_type.title}",
                    callback_data=types_cb.new(id=_type.type_id, action='select_type')),
            )

        if page != 1:     
            markup.add(
                types.InlineKeyboardButton(
                    "BACK",
                    callback_data=types_cb.new(id="--1", action='back_types')),
            )
        
        if is_next:
            markup.add(
                types.InlineKeyboardButton(
                    "NEXT",
                    callback_data=types_cb.new(id="++1", action='next_types')),
            )

        markup.add(
                types.InlineKeyboardButton(
                    "Cancel",
                    callback_data=types_cb.new(id="cancel", action='cancel')),
            )

        return markup

class CommandDefinitionTypes(DefinitionTypeMixin):
    
    def __init__(self, bot, dp: Dispatcher ,log) -> None:
        self.LOG = log
        self.bot = bot

        self.valid_commands = {
            "Count": self.on_count,
            "Add": self.on_add,
            "Remove": self.on_remove,
            "List": self.on_list
        }

        self.types_commands = {
             "Edit": self.on_type_edit
        }
             
        dp.register_message_handler(self.on_new_type, state=Form.type_name)
        dp.register_message_handler(self.on_detail_type, lambda message: message.text not in "Add", state=Form.sub_detail_type_command)
        dp.register_message_handler(self.invalid_detail_type, lambda message: message.text not in ("Add", *self.types_commands), state=Form.sub_detail_type_command)

        dp.register_message_handler(DefinitionTypeMixin.update_type_name, state=Form.update_type_name)

        dp.register_callback_query_handler(self.on_next_types, types_cb.filter(action='next_types'))

        dp.register_callback_query_handler(DefinitionTypeMixin.on_back_types, types_cb.filter(action='back_types'))
        dp.register_callback_query_handler(DefinitionTypeMixin.on_cancel, types_cb.filter(action='cancel'), state=Form.sub_detail_type_command)
        
        # dp.register_message_handler(self.on_remove_role, state=Form.remove_role_name)
        dp.register_message_handler(self.subcommand, lambda message: message.text in list(self.valid_commands), state=Form.sub_type_command)
        dp.register_message_handler(self.invalid_subcommand, lambda message: message.text not in list(self.valid_commands), state=Form.sub_type_command)

        dp.register_callback_query_handler(self.on_select_type, types_cb.filter(action='select_type'))
    

    async def invalid_detail_type(self, message: types.Message, state: FSMContext):
        await self.close(message, "Canceled", state)

    async def on_detail_type(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"subcommand process {message.text}...")
        cmd = self.types_commands.get(message.text)
        if cmd:
            await cmd(message, state)
        else:
            await self.close(message, "canceled", state)
            
    async def run(self, user: User, role: Role, message: types.Message):
        self.LOG.info("run", details={"command": "/types"})

        await Form.sub_type_command.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(*self.valid_commands)

        await message.reply("next subcommand", reply_markup=markup)

    async def invalid_subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info("subcommand process types ...")
        await state.finish()
        await message.reply('Oops', reply_markup=types.ReplyKeyboardRemove())
    
    
    async def subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"subcommand process {message.text}...")
        cmd = self.valid_commands[message.text]
        await cmd(message, state)
    
    async def on_add(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        await Form.type_name.set()

        await message.answer("?")
        
    async def on_new_type(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"create a new type: {message.text}")

        typeExist = await DefinitionType.exists(title=message.text.lower())

        if typeExist:
            await self.close(message, "Такой тип существует", state)
        else:
            await (await DefinitionType.create(title=message.text.lower())).save()
            await self.close(message, "ok", state)
    
    async def on_count(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        _types = await DefinitionType.all()

        await self.close(message, str(len(_types)), state)
    
    
    async def on_list(self, message: types.Message, state: FSMContext):
        await state.finish()
        await self.def_first_list(message, state)

    async def on_remove(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        await Form.remove_type_name.set()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        _types = [ r.title for r in await DefinitionType.all() ]
        
        markup.add(*_types)

        await message.reply("select", reply_markup=markup)


    async def on_remove_role(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"remove role: {message.text} ...")

        await Role.filter(title=message.text).delete()

        await self.close(message, "removed", state)
    
    async def close(self, message: types.Message, answer: str, state: FSMContext):
        self.LOG.info(f"close {message.text} ...")
        await state.finish()
        await message.answer(answer, reply_markup=types.ReplyKeyboardRemove())