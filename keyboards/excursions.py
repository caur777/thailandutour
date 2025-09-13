# keyboards/excursions.py
from aiogram.utils.keyboard import InlineKeyboardBuilder as _InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup as _InlineKeyboardMarkup

def get_excursion_categories_keyboard(categories) -> _InlineKeyboardMarkup:
    """
    Ожидает список категорий нового формата:
    categories = [{"id": str, "title": str, "tour": [...]}, ...]
    """
    # Страховка от неверного аргумента: если передали весь dict, достанем список
    if isinstance(categories, dict):
        categories = categories.get("category", [])

    kb = _InlineKeyboardBuilder()
    for cat in categories or []:
        cid = cat.get("id")
        title = cat.get("title", "Без названия")
        if not cid:
            continue
        kb.button(text=title, callback_data=f"category:{cid}")

    kb.button(text="⬅️ Назад", callback_data="show_catalog")

    kb.adjust(1)
    return kb.as_markup()
