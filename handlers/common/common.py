from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from config import MANAGER_USERNAME
from keyboards.main_menu import main_menu_keyboard

import os

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        text="Здесь всё просто: выбирайте, что нужно, я подскажу дальше:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
    except Exception:
        pass

    # Просто отправляем клавиатуру без текста
    await callback_query.message.answer(
        text="Здесь всё просто: выбирайте, что нужно, я подскажу дальше:",
        reply_markup=main_menu_keyboard
    )

    await callback_query.answer()
