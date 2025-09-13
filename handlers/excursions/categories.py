# handlers/excursions/categories.py
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from utils.loader import load_excursions
from utils.ux import show_screen_text

categories_router = Router()

@categories_router.callback_query(lambda cq: cq.data and cq.data.startswith("category:"))
async def handle_category_callback(query: CallbackQuery, state: FSMContext):
    _, category_id = query.data.split(":", 1)

    data = load_excursions()
    categories = data.get("category", []) if isinstance(data, dict) else []

    category = next((c for c in categories if c.get("id") == category_id), None)
    if not category:
        await show_screen_text(query, state, "Категория не найдена.")
        return

    tours = category.get("tour", []) or []

    kb = InlineKeyboardBuilder()
    for t in tours:
        t_id = t.get("id")
        t_title = t.get("title", "Без названия")
        if t_id:
            kb.button(text=t_title, callback_data=f"details:{category_id}:{t_id}")

    # Только «Назад» — возвращаемся к списку категорий
    kb.button(text="🔙 Назад", callback_data="show_catalog_list")
    kb.adjust(1)

    await show_screen_text(query, state, "📍 Выберите тур:", reply_markup=kb.as_markup())
