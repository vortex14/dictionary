from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.callback_data import CallbackData
from models import User, get_user, ADMIN, UNKNOWN
from aiogram.dispatcher import FSMContext
from bot.command import CommandMixin
from models import User, Role
from cgitb import handler
from devtools import debug
from typing import List

class Form(StatesGroup):
    subcommand = State()

    user_id = State()
    role_id = State()
    
    count = State()
    page = State()


posts_cb = CallbackData('post', 'id', 'action')  # post:<id>:<action>

PER_COUNT=2

def get_role_list(roles: List[Role]) -> types.InlineKeyboardMarkup:
    """
    Generate keyboard with list of Users
    """
    markup = types.InlineKeyboardMarkup()

    for role in roles:
        markup.add(
            types.InlineKeyboardButton(
                f"{role.title}",
                callback_data=posts_cb.new(id=role.role_id, action='select_role')),
        )

    return markup


def get_user_list(page: int, users: List[User], is_next: bool) -> types.InlineKeyboardMarkup:
    """
    Generate keyboard with list of Users
    """
    markup = types.InlineKeyboardMarkup()
    skip = 0

    if page != 1: skip = (page - 1) * PER_COUNT

    for user in users[skip: skip + PER_COUNT]:
        markup.add(
            types.InlineKeyboardButton(
                f"{user.last_name} {user.first_name}",
                callback_data=posts_cb.new(id=user.telegram_id, action='select_user')),
        )

    if page != 1:     
        markup.add(
            types.InlineKeyboardButton(
                "BACK",
                callback_data=posts_cb.new(id="-1", action='back_page')),
        )
    
    if is_next:
        markup.add(
            types.InlineKeyboardButton(
                "NEXT",
                callback_data=posts_cb.new(id="+1", action='next_page')),
        )

    return markup

class CommandUsers(CommandMixin):
    
    def __init__(self, bot, dp: Dispatcher ,log) -> None:
        self.LOG = log
        self.bot = bot

        self.valid_commands = {
            "Count": self.on_count,
            "List": self.on_first_list,
            # "Add": self.on_add,
            # "Remove": self.on_remove,
            # "Change": self.on_change
        }

        dp.register_callback_query_handler(self.select_user, posts_cb.filter(action='select_user'))
        dp.register_callback_query_handler(self.select_role, posts_cb.filter(action='select_role'))

        dp.register_callback_query_handler(self.next_users, posts_cb.filter(action='next_page'))
        dp.register_callback_query_handler(self.back_users, posts_cb.filter(action='back_page'))
             
        dp.register_message_handler(self.subcommand, lambda message: message.text in self.valid_commands, state=Form.subcommand)
        dp.register_message_handler(self.invalid_subcommand, lambda message: message.text not in self.valid_commands, state=Form.subcommand)

    

    async def select_user(self, query: types.CallbackQuery, state: FSMContext):
        user_id = int(query.data.split(":")[1])
        user = await User.filter(telegram_id=user_id).first()
        role = await user.role
        self.LOG.info("Selected User", details=dict(user))

        roles = await Role.all()
        async with state.proxy() as data:
            data.update(user_id=user_id)

            await query.message.edit_text(f"Текущая роль: {role.title}", reply_markup=get_role_list(roles))

    
    async def select_role(self, query: types.CallbackQuery, state: FSMContext):
        role_id = int(query.data.split(":")[1])
        role = await Role.filter(role_id=role_id).first()
        async with state.proxy() as data:

            self.LOG.info("select_role", details=data)
            user = await User.filter(telegram_id=data["user_id"]).first()
            user.role = role
            await user.save()
            self.LOG.info("Selected a new role", details={"firstname": user.first_name, "lastname": user.last_name, "new_role": role.title})
            await query.message.delete()

        await self.close(query.message, "Ok", state)
    
    async def next_users(self, query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_next = data["count"] > (data["page"] + 1) * PER_COUNT
            self.LOG.info(f"================ next {is_next} ===========", details=data)
            next_page = data["page"] + 1
            data.update(page=next_page)
            
            users = await User.all()
            await query.message.edit_text("->", reply_markup=get_user_list(next_page, users, is_next))
        

    async def back_users(self, query: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            is_back = data["page"] != 1
            next_page = data["page"] - 1

            self.LOG.info(f"================ back to {next_page} ===========", details=data)

            data.update(page=next_page)

            users = await User.all()
            await query.message.edit_text("<-", reply_markup=get_user_list(next_page, users, is_back))

    async def run(self, user: User, role: Role, message: types.Message):
        self.LOG.info("run", details={"command": "/users", "user": user.first_name, "id": user.telegram_id, "role": role.title})

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
        self.LOG.info(f"subcommand process /user/{message.text}...")
        cmd = self.valid_commands[message.text]
        await cmd(message, state)
        
        # current_state = await state.get_state()
        # await state.finish()

        # await Form.next()
        # await state.update_data(page=int(500))

        # await Form.next()

        # await message.reply('ok', reply_markup=get_keyboard(1))

    
    async def on_count(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        users = await User.all()

        await self.close(message, str(len(users)), state)
    
    async def on_first_list(self, message: types.Message, state: FSMContext):
        self.LOG.info(f"process {message.text} ...")
        users = await User.all()
        count = len(users)

        await state.finish()

        await state.update_data(page=1, count=count)

        await message.reply('ok', reply_markup=get_user_list(1, users, True))
    
    async def change_status(self):
        pass

    async def create(self):
        pass