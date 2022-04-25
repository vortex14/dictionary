from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram import Bot, Dispatcher, executor, types

from aiogram.dispatcher import FSMContext
from utils import MimeTypeFilter, fetch
from models import User, Role, Term
from typing import List, Union
import aiohttp
import os

class Form(StatesGroup):
    page = State()
    count = State()
    file = State()

    term_name = State()
    search_term = State()
    remove_term_name = State()
    sub_term_command = State()

posts_cb = CallbackData('post', 'id', 'action')  # post:<id>:<action>

PER_COUNT=int(os.environ["PAGE_TERM_PER_COUNT"])
MAX_SEARCH_OUTPUT=int(os.environ["MAX_SEARCH_OUTPUT"])

class CommandTerms:
    
    def __init__(self, bot, dp: Dispatcher ,log) -> None:
        self.LOG = log
        self.bot = bot

        self.valid_commands = {
            "Count": self.on_count,
            "Add": self.on_add,
            "List": self.on_first_list,
            "Upload": self.upload,
            "Find": self.find,
            # "Remove": self.on_remove,
            # "List": self.on_list
        }

             
        dp.register_message_handler(self.on_new_term, state=Form.term_name)
        dp.register_message_handler(self.on_remove_term, state=Form.remove_term_name)

        dp.filters_factory.bind(MimeTypeFilter, event_handlers=[dp.message_handlers])
        dp.register_message_handler(self.on_upload_file, content_types=types.ContentTypes.DOCUMENT, mime_type=["text/plain", "text/csv"], state=Form.file)

        dp.register_message_handler(self.on_search, state=Form.search_term)

        dp.register_callback_query_handler(self.next_terms, posts_cb.filter(action='next_terms'))
        dp.register_callback_query_handler(self.back_terms, posts_cb.filter(action='back_terms'))

        dp.register_message_handler(self.subcommand, lambda message: message.text in list(self.valid_commands), state=Form.sub_term_command)
        dp.register_message_handler(self.invalid_subcommand, lambda message: message.text not in list(self.valid_commands), state=Form.sub_term_command)

    
    async def on_search(self, message: types.Message, state: FSMContext):
        finded = await Term.filter(title__icontains=message.text)
        result = "\n".join([it.title for it in finded[:MAX_SEARCH_OUTPUT]])
        await self.close(message, f"Найдено: {len(finded)}\n{result}", state)

    async def find(self, message: types.Message, state: FSMContext):
        await Form.search_term.set()
        await message.answer("?", reply_markup=types.ReplyKeyboardRemove() )
        
    async def upload(self, message: types.Message, state: FSMContext):
        await Form.file.set()
        await message.answer("Жду файл", reply_markup=types.ReplyKeyboardRemove() )

    async def on_upload_file(self, message: types.Message, state: FSMContext):
        self.LOG.info("on file", details={"file": message.document.file_name, "size": message.document.file_size, "userfname": message.from_user.full_name})
        data = await message.document.get_file()
        url = f"https://api.telegram.org/file/bot{os.environ['API_TELEGRAM_BOT_TOKEN']}/{data['file_path']}"
        self.LOG.info("download file", details={"url": url, **dict(data), **dict(message.from_user)})
        async with aiohttp.ClientSession() as session:
            data = (await fetch(session, url)).split()
            exists = 0
            saved = 0

            for it in data:
                if not (await Term.exists(title=it.lower())):
                    await Term.create(title=it.lower())
                    saved += 1
                else:
                    exists += 1

            await message.answer(f"Обработано: {len(data)}, Добавлено: {saved}, Дубликаты: {exists}")

        await state.finish()    

    async def run(self, user: User, role: Role, message: types.Message):
        self.LOG.info("run", details={"command": "/terms"})

        await Form.sub_term_command.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(*self.valid_commands)

        await message.reply("next subcommand", reply_markup=markup)


        
    async def next_terms(self, query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_next = data["count"] > (data["page"] + 1) * PER_COUNT
            self.LOG.info(f"================ next {is_next} ===========", details=data)
            next_page = data["page"] + 1
            data.update(page=next_page)
            
            terms = await Term.all()
            await query.message.edit_text("->", reply_markup=self.get_term_list(next_page, terms, is_next))
        

    async def back_terms(self, query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_back = data["page"] != 1
            next_page = data["page"] - 1

            self.LOG.info(f"================ back to {next_page} ===========", details=data)

            data.update(page=next_page)

            terms = await Term.all()
            await query.message.edit_text("<-", reply_markup=self.get_term_list(next_page, terms, is_back))
    
    
    async def invalid_subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info("subcommand process terms ...")
        await state.finish()
        await message.reply('Oops', reply_markup=types.ReplyKeyboardRemove())
    
    
    async def subcommand(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"subcommand process {message.text}...")
        cmd = self.valid_commands[message.text]
        await cmd(message, state)
    
    async def on_add(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        await Form.term_name.set()

        await message.answer("?", reply_markup=types.ReplyKeyboardRemove() )
        
    async def on_new_term(self, message: types.Message, state: FSMContext):
        new_term = message.text.lower()
        self.LOG.info(f"create a new term: {new_term}")

        roleExist = await Term.exists(title=new_term)

        match roleExist:
            case True:
                await self.close(message, f'Термин "{new_term}" существует', state)
            case False:
                await (await Term.create(title=new_term)).save()
                await self.close(message, f'Термин "{new_term}" добавлен', state)
    
    async def on_count(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        roles = await Term.all()

        await self.close(message, str(len(roles)), state)
    
    
    async def on_list(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")

        roles = "".join( [ r.title + "\n" for r in await Role.all() ] )

        await self.close(message, roles or "Не найдено", state)

    async def on_remove(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        await Form.remove_role_name.set()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        roles = [ r.title for r in await Role.all() ]
        
        markup.add(*roles)

        await message.reply("select", reply_markup=markup)

        # await self.close(message, "done", state)

    async def on_remove_term(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"remove term: {message.text} ...")

        await Role.filter(title=message.text).delete()

        await self.close(message, "removed", state)
    
    async def close(self, message: types.Message, answer: str, state: FSMContext):
        self.LOG.info(f"close {message.text} ...")
        await state.finish()
        await message.answer(answer, reply_markup=types.ReplyKeyboardRemove())


    async def on_first_list(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        terms = await Term.all()
        count = len(terms)

        await state.finish()

        await state.update_data(page=1, count=count)
        await message.reply("Добавленные термины", reply_markup=types.ReplyKeyboardRemove())
        await message.reply(":", reply_markup=self.get_term_list(1, terms, True))


    def get_term_list(self, page: int, terms: List[Term], is_next: bool) -> types.InlineKeyboardMarkup:
        """
        Generate keyboard with list of Terms
        """
        markup = types.InlineKeyboardMarkup()
        skip = 0

        if page != 1: skip = (page - 1) * PER_COUNT

        for term in terms[skip: skip + PER_COUNT]:
            markup.add(
                types.InlineKeyboardButton(
                    f"{term.title}",
                    callback_data=posts_cb.new(id=term.term_id, action='select_term')),
            )

        if page != 1:     
            markup.add(
                types.InlineKeyboardButton(
                    "BACK",
                    callback_data=posts_cb.new(id="-1", action='back_terms')),
            )
        
        if is_next:
            markup.add(
                types.InlineKeyboardButton(
                    "NEXT",
                    callback_data=posts_cb.new(id="+1", action='next_terms')),
            )

        markup.add(
                types.InlineKeyboardButton(
                    "Cancel",
                    callback_data=posts_cb.new(id="cancel", action='cancel')),
            )

        return markup