from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram import Bot, Dispatcher, executor, types

from aiogram.dispatcher import FSMContext
from sqlalchemy import DefaultClause
from utils import MimeTypeFilter, fetch, string_to_uuid, get_hash, remove_html_p, remove_html
from models import User, Role, Term, Definition, DefinitionType
from .types import DefinitionTypeMixin, Form as DefTypeForm
from typing import List, Union
import aiohttp
import os

class Form(DefTypeForm):
    page = State()
    count = State()
    def_file = State()

    def_term = State()
    def_list_term = State()
    exist_term_name = State()
    def_content = State()
    def_edited_content = State()
    search_def = State()
    sub_def_command = State()
    sub_def_edit_command = State()

posts_cb = CallbackData('post', 'id', 'action')  # post:<id>:<action>

PER_COUNT=int(os.environ["PAGE_DEF_PER_COUNT"])*5
MAX_SEARCH_OUTPUT=int(os.environ["MAX_SEARCH_OUTPUT"])

class CommandDefinition(DefinitionTypeMixin):
    
    def __init__(self, bot, dp: Dispatcher ,log) -> None:
        self.LOG = log
        self.bot = bot

        self.valid_commands = {
            "Count": self.on_count,
            "Add": self.on_add,
            "Show": self.on_show,
            "Cancel": self.on_cancel,
            "List": self.on_def_list,
            "Upload": self.upload,
            # "Find": self.find,
            # "Remove": self.on_remove,
            # "List": self.on_list
        }

        self.defs_commands = {
            "Edit": self.on_edit,
            "Remove": self.on_remove,
            "Type": self.on_type,
            "Cancel": self.on_cancel
        }

        self.types_commands = {
             "Edit": DefinitionTypeMixin.on_type_edit,
             "Add": self.add_type
        }

             
        dp.register_message_handler(self.on_check_term, state=Form.exist_term_name)
        dp.register_message_handler(self.on_def_list_def, state=Form.def_list_term)
        dp.register_message_handler(self.on_new_def, state=Form.def_content)
        dp.register_message_handler(self.on_edited_def, state=Form.def_edited_content)
        dp.register_message_handler(self.on_def_term, state=Form.def_term)


        # select_def


        # dp.register_message_handler(self.on_remove_term, state=Form.remove_term_name)

        # dp.filters_factory.bind(MimeTypeFilter, event_handlers=[dp.message_handlers])
        dp.register_message_handler(self.on_upload_file, content_types=types.ContentTypes.DOCUMENT, mime_type=["text/plain", "text/csv"], state=Form.def_file)

        # dp.register_message_handler(self.on_search, state=Form.search_term)

        dp.register_callback_query_handler(self.next_defs, posts_cb.filter(action='next_defs'))
        dp.register_callback_query_handler(self.back_defs, posts_cb.filter(action='back_defs'))
        dp.register_callback_query_handler(self.on_cancel, posts_cb.filter(action='cancel'))

        dp.register_callback_query_handler(self.on_select_def, posts_cb.filter(action='select_def'))
        dp.register_callback_query_handler(self.on_select_type, posts_cb.filter(action='select_type'))
        dp.register_message_handler(self.add_type, lambda message: message.text in "Add", state=Form.sub_detail_type_command)

        dp.register_message_handler(self.subcommand, lambda message: message.text in list(self.valid_commands), state=Form.sub_def_command)
        dp.register_message_handler(self.invalid_subcommand, lambda message: message.text not in list(self.valid_commands), state=Form.sub_def_command)

        dp.register_message_handler(self.def_subcommand, lambda message: message.text in list(self.defs_commands), state=Form.sub_def_edit_command)
        dp.register_message_handler(self.invalid_subcommand, lambda message: message.text not in list(self.defs_commands), state=Form.sub_def_edit_command)

    
    async def on_search(self, message: types.Message, state: FSMContext):
        finded = await Term.filter(title__icontains=message.text)
        result = "\n".join([it.title for it in finded[:MAX_SEARCH_OUTPUT]])
        await self.close(message, f"Найдено: {len(finded)}\n{result}", state)

    async def find(self, message: types.Message, state: FSMContext):
        await Form.search_term.set()
        await message.answer("?", reply_markup=types.ReplyKeyboardRemove() )
        
    async def upload(self, message: types.Message, state: FSMContext):
        await Form.def_file.set()
        await message.answer("Жду файл", reply_markup=types.ReplyKeyboardRemove() )

    async def on_upload_file(self, message: types.Message, state: FSMContext):
        self.LOG.info("on file", details={"file": message.document.file_name, "size": message.document.file_size, "userfname": message.from_user.full_name})
        data = await message.document.get_file()
        url = f"https://api.telegram.org/file/bot{os.environ['API_TELEGRAM_BOT_TOKEN']}/{data['file_path']}"
        self.LOG.info("download file", details={"url": url, **dict(data), **dict(message.from_user)})
        async with aiohttp.ClientSession() as session:
            data = (await fetch(session, url)).split("\n")
            self.LOG.info(f'Получен файл', details={"count": len(data)})
            term_exists = 0
            def_exists = 0
            saved_term = 0
            saved_def = 0
            error_line = 0

            for it in data:
                try:
                    term, _def = it.split(":")
                except:
                    error_line += 1
                    continue

                if not (await Term.exists(title=term.lower())):

                    term = await Term.create(title=it.lower())
                    # term = await Term.filter(title=data["term"]).first()
                    definition = Definition(content=_def, term=term)
                    await definition.save()
                    
                    saved_def += 1
                    saved_term += 1

                else:
                    term = await Term.filter(title=term.lower()).first()
                    is_exist = False
                    new_def_content =  _def.lower()
                    definition = Definition(content=new_def_content, term=term)
                    async for _def in term.definitions:
                        if string_to_uuid(new_def_content) == string_to_uuid(_def.content):
                            is_exist = True
                            break
                    if not is_exist:
                        saved_def += 1
                        await definition.save()
                    else:
                        def_exists += 1    
                    
                    term_exists += 1

            await message.answer(f"Обработано: {len(data)}, Добавлено терминов: {saved_term}\nДобавлено определений: {saved_def}, Ошибок в линиях: {error_line}\nДубликатов определений: {def_exists}, Найденных терминов: {term_exists}")

        await state.finish()    

    async def run(self, user: User, role: Role, message: types.Message):
        self.LOG.info("run", details={"command": "/def"})

        await Form.sub_def_command.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(*self.valid_commands)

        await message.reply("next subcommand", reply_markup=markup)


    async def add_type(self, message: types.Message, state: FSMContext ):
        sd = await state.get_data()
        self.LOG.info("add type", details={**dict(sd)})
        _type = await DefinitionType.filter(type_id=sd["type_id"]).first()
        await Definition.filter(id=sd["def_id"]).update(type=_type)
        await self.close(message, "Тип прикреплён к определению", state)


    
    async def on_select_def(self, query: types.CallbackQuery, state: FSMContext):
        def_id = int(query.data.split(":")[1])
        current_state = await state.get_data()
        await state.update_data(def_id=def_id)
        _def = await Definition.filter(id=def_id).first()
        self.LOG.info("select def", details={"term_id": current_state["term_id"], **dict(_def)})

        await Form.sub_def_edit_command.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(*self.defs_commands)
        
        content = _def.content
        if _def.type:
            _type = await _def.type
            content = f"Привязан к типу: {_type.title} \n{content}"

        await query.message.answer(content, reply_markup=markup, parse_mode="html")

        
    async def next_defs(self, query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_next = data["count"] > (data["page"] + 1) * PER_COUNT
            self.LOG.info(f"================ next {is_next} ===========", details=data)
            next_page = data["page"] + 1
            data.update(page=next_page)
            term = await Term.filter(title=data["term"]).first()
            defs = await Definition.filter(term=term.term_id)
            await query.message.edit_text("->", reply_markup=self.get_def_list(next_page, defs, is_next))
        

    async def back_defs(self, query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_back = data["page"] != 1
            next_page = data["page"] - 1

            self.LOG.info(f"================ back to {next_page} ===========", details=data)

            data.update(page=next_page)

            term = await Term.filter(title=data["term"]).first()
            defs = await Definition.filter(term=term.term_id)
            await query.message.edit_text("<-", reply_markup=self.get_def_list(next_page, defs, is_back))
    
    async def invalid_subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info("subcommand process defs ...")
        await state.finish()
        await message.reply('Oops', reply_markup=types.ReplyKeyboardRemove())
    
    
    async def subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"subcommand process {message.text}...")
        cmd = self.valid_commands[message.text]
        await cmd(message, state)
    
    
    async def def_subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"subcommand process {message.text}...")
        cmd = self.defs_commands[message.text]
        await cmd(message, state)
    


    async def on_show(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        await Form.def_term.set()

        await message.answer("Введите термин для отображения всех терминов", reply_markup=types.ReplyKeyboardRemove() )
    
    async def on_add(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        await Form.exist_term_name.set()

        await message.answer("К какому термину добавить определение?", reply_markup=types.ReplyKeyboardRemove() )
        
    async def on_def_term(self, message: types.Message, state: FSMContext):
        term_name = message.text.lower()
        self.LOG.info(f"show all def for term: {term_name}")

        termExist = await Term.exists(title=term_name)

        match termExist:
            case True:
                await state.finish()
                term = await Term.filter(title=term_name).first()

                data = "\n\n".join( [f'{"Тип неопределён " if  not await it.type else f"Тип: " + (await it.type).title }\n{remove_html_p(it.content)}' for it in await Definition.filter(term=term.term_id)] )
                if data:
                    await message.answer(data, reply_markup=types.ReplyKeyboardRemove(), parse_mode="html" )
                else:
                    await message.answer("Не найдены определения")
            case False:
                await self.close(message, f'Термин "{term_name}"не создан', state)
    
    async def on_check_term(self, message: types.Message, state: FSMContext):
        term_name = message.text.lower()
        self.LOG.info(f"create a new def for term: {term_name}")

        termExist = await Term.exists(title=term_name)

        match termExist:
            case True:
                await Form.def_content.set()
                await state.update_data(term=term_name)
                await message.answer("Какое определение?", reply_markup=types.ReplyKeyboardRemove() )
            case False:
                await self.close(message, f'Термин "{term_name}"не создан', state)
    
    async def on_new_def(self, message: types.Message, state: FSMContext):
        def_content = message.html_text
        hash_data = get_hash(def_content.lower())

        async with state.proxy() as data:
            term = await Term.filter(title=data["term"]).first()
            check = await Definition.filter(hash_data=hash_data).first()

            if check:
                self.LOG.warning("такое определение существует", details={"content": def_content, "term": data["term"]})
                
                return await self.close(message, "такое определение существует", state)

            definition = Definition(content=def_content, hash_data=hash_data, term=term)
            await definition.save()

            await Form.sub_def_edit_command.set()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(*self.defs_commands)

            await state.update_data(def_id=definition.id)

            await message.answer(f'Для термина "{term.title}" добавлено новое определение:\n{def_content}', reply_markup=markup, parse_mode="html")
            
    
    async def on_count(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        defs = await Definition.all()

        await self.close(message, str(len(defs)), state)
    
    
    async def on_list(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        roles = "".join( [ r.title + "\n" for r in await Role.all() ] )

        await self.close(message, roles or "Не найдено", state)

    async def on_cancel(self, message: types.Message, state: FSMContext):
        self.LOG.info("cancel ...")
        await state.finish()
        await message.reply("canceled", reply_markup=types.ReplyKeyboardRemove())
        # await self.close(message, "canceled", state)

    async def on_edit(self, message: types.Message, state: FSMContext):
        await Form.def_edited_content.set()
        await message.answer("Какое новое определение?", reply_markup=types.ReplyKeyboardRemove() )

    async def on_edited_def(self, message: types.Message, state: FSMContext):
        current_state = await state.get_data()
        def_id = current_state["def_id"]
        await state.finish()

        self.LOG.info("new def", details={"id": def_id, "content": message.text})

        _def = await Definition.filter(id=int(def_id)).first()
        self.LOG.info("current def ", details={"old content": _def.content, "new content": message.text.lower()})
 
        if string_to_uuid(_def.content) == string_to_uuid(message.text.lower()):
            return await self.close(message, "Такое определение уже было", state)

        await Definition.filter(id=def_id).update(content=message.text.lower())

        await message.answer("Обновлено", reply_markup=types.ReplyKeyboardRemove())
    
    async def on_type(self, message: types.Message, state: FSMContext):
        def_types = await DefinitionType().all()
        if len(def_types) == 0:
            return await self.close(message, "Типов для определений нет. Добавить /types ?", state)

        def_id = (await state.get_data())["def_id"]
        await state.finish()
        await state.update_data(def_id=def_id)
        await self.def_first_list(message, state)
    
    async def on_remove(self, message: types.Message, state: FSMContext):
        current_state = await state.get_data()
        def_id = current_state["def_id"]
        is_next = current_state["count"] > (current_state["page"] + 1) * PER_COUNT
        await state.finish()

        await Definition.filter(id=def_id).delete()

        term = await Term.filter(term_id=current_state["term_id"]).first()
        defs = await Definition.filter(term=term.term_id)
        await state.update_data(page=1, def_id=def_id, count=len(defs), term_id=term.term_id)

        # await message.message.edit_text("<-", reply_markup=self.get_def_list(next_page, defs, is_back))

        self.LOG.info("remove def", details={"id": def_id, **current_state, "count_defs": len(defs)})

        await message.answer("removed",reply_markup=self.get_def_list(1, defs, is_next))
    
    async def close(self, message: types.Message, answer: str, state: FSMContext):
        self.LOG.info(f"close {message.text} ...")
        await state.finish()
        await message.answer(answer, reply_markup=types.ReplyKeyboardRemove())


    async def on_def_list_def(self, message: types.Message, state: FSMContext):
        term_name = message.text.lower()
        self.LOG.info(f"Check exists term: {term_name}")

        termExist = await Term.exists(title=term_name)

        match termExist:
            case True:
                await state.finish()
                
                term = await Term.filter(title=term_name).first()
                defs = await Definition.filter(term=term.term_id)
                await state.update_data(page=1, count=len(defs), term=term_name, term_id=term.term_id)

                await message.reply("Добавленные определения. Для добавления типа определения необходимо его выбрать из списка.", reply_markup=types.ReplyKeyboardRemove())
                await message.reply(":", reply_markup=self.get_def_list(1, defs, True))
            case False:
                await self.close(message, f'Термин "{term_name}"не создан', state)
    
    
    async def on_def_list(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        await Form.def_list_term.set()

        await message.answer("Введите термин для отображения списка определений", reply_markup=types.ReplyKeyboardRemove() )


    def get_def_list(self, page: int, defs: List[Definition], is_next: bool) -> types.InlineKeyboardMarkup:
        """
        Generate keyboard with list of Defs
        """
        markup = types.InlineKeyboardMarkup()
        skip = 0

        if page != 1: skip = (page - 1) * PER_COUNT

        for _def in defs[skip: skip + PER_COUNT]:
            markup.add(
                types.InlineKeyboardButton(
                    f"{remove_html(_def.content)}",
                    callback_data=posts_cb.new(id=_def.id, action='select_def')),
            )

        if page != 1:     
            markup.add(
                types.InlineKeyboardButton(
                    "BACK",
                    callback_data=posts_cb.new(id="-1", action='back_defs')),
            )
        
        if is_next:
            markup.add(
                types.InlineKeyboardButton(
                    "NEXT",
                    callback_data=posts_cb.new(id="+1", action='next_defs')),
            )

        markup.add(
                types.InlineKeyboardButton(
                    "Cancel",
                    callback_data=posts_cb.new(id="cancel", action='cancel')),
            )

        return markup