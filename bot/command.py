from aiogram.dispatcher import FSMContext
from aiogram import types


class CommandMixin:

    async def close(self, message: types.Message, answer: str, state: FSMContext):
        self.LOG.info(f"close {message.text} ...")
        await state.finish()
        await message.answer(answer, reply_markup=types.ReplyKeyboardRemove() )
        # await message.delete_reply_markup()