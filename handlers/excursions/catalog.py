# handlers/excursions/catalog.py
from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from config import MANAGER_USERNAME
from utils.loader import load_excursions
from keyboards.excursions import get_excursion_categories_keyboard
from utils.ux import show_screen_photo, show_screen_text

catalog_router = Router()

@catalog_router.callback_query(lambda cq: cq.data and cq.data.lower() == "show_catalog")
async def show_catalog_handler(query: CallbackQuery, state: FSMContext):
    photo = FSInputFile("static/excursions_cover.png")
    caption = (
        "📋 <b>Каталог туров по Пхукету</b>\n\n"
        "Только проверенные программы, надёжные партнёры и внимание к деталям — "
        "чтобы вы могли отдыхать спокойно.\n\n"
        "Выбирайте то, что по душе, и бронируйте прямо в боте.\n\n"
        f'Есть вопросы — <a href="https://t.me/{MANAGER_USERNAME}">мы всегда на связи</a> 💬'
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Каталог туров", callback_data="show_catalog_list")],
        [InlineKeyboardButton(text="ℹ️ Важная информация", callback_data="important_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

    await show_screen_photo(
        query, state,
        photo=photo,
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

@catalog_router.callback_query(lambda cq: cq.data == "show_catalog_list")
async def show_catalog_list(query: CallbackQuery, state: FSMContext):
    data = load_excursions()
    categories = data.get("category", []) if isinstance(data, dict) else []

    keyboard = get_excursion_categories_keyboard(categories)

    text = (
        "🌊 Морские туры — Пхи-Пхи, острова, белый песок, прозрачные каяки.\n"
        "🏞️ Наземные туры — Краби, пещеры, озеро Чео-Лан.\n"
        "⚡️ Приключения — рафтинг, багги, зиплайн, слоны (этичные парки).\n\n"
        "Выберите категорию ниже 👇"
    )

    await show_screen_text(query, state, text, reply_markup=keyboard)