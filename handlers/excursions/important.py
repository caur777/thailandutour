# handlers/excursions/important.py
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from pathlib import Path
import logging

from utils.ux import show_screen_text

important_router = Router()
IMPORTANT_DIR = Path(__file__).parent.parent.parent / "data" / "important"

def _menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🧭 Процесс бронирования и оплаты", callback_data="imp:process")
    kb.button(text="🏨 Размещение на острове Пхипхи", callback_data="imp:phi")
    kb.button(text="⛺ Размещение на озере Чеолан", callback_data="imp:cheo")
    kb.button(text="↩️ Политика отмены", callback_data="imp:cancellation")
    kb.button(text="📂 Перейти к каталогу туров", callback_data="show_catalog_list")
    kb.button(text="💛 Главное меню", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()

def _back_keyboard(back_cb: str | None):
    kb = InlineKeyboardBuilder()
    # если пришли из тура с контекстом — ведём назад в цены тура,
    # иначе — в меню "Важная информация"
    kb.button(text="⬅️ Назад", callback_data=back_cb or "important_menu")
    kb.button(text="📂 Перейти к каталогу туров", callback_data="show_catalog_list")
    kb.button(text="💛 Главное меню", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()

@important_router.callback_query(lambda cq: cq.data == "important_menu")
async def important_menu(query: CallbackQuery, state: FSMContext):
    text = (
        "ℹ️ <b>Важная информация</b>\n\n"
        "Выберите раздел: процесс бронирования и оплаты, варианты размещения, политика отмены."
    )
    await show_screen_text(query, state, text, reply_markup=_menu_keyboard(), parse_mode="HTML")

@important_router.callback_query(lambda cq: cq.data and cq.data.startswith("imp:"))
async def important_section(query: CallbackQuery, state: FSMContext):
    # Поддерживаем форматы:
    # imp:phi
    # imp:phi:<cat_id>:<tour_id>   ← из цен конкретного тура
    tokens = query.data.split(":")
    # tokens[0] = "imp"
    section = tokens[1] if len(tokens) > 1 else ""
    cat_id = tokens[2] if len(tokens) > 2 else None
    tour_id = tokens[3] if len(tokens) > 3 else None

    files = {
        "process":      "process.md",
        "phi":          "pp_accommodation.md",
        "cheo":         "cheowlan_accommodation.md",
        "cancellation": "cancellation.md",
    }
    fname = files.get(section)
    if not fname:
        logging.warning("Unknown important section: %r", section)
        return

    try:
        text = (IMPORTANT_DIR / fname).read_text(encoding="utf-8")
    except Exception as e:
        logging.exception("Failed to read important file %s: %s", fname, e)
        return

    back_cb = f"tour:prices:{cat_id}:{tour_id}" if (cat_id and tour_id) else None
    await show_screen_text(query, state, text, reply_markup=_back_keyboard(back_cb), parse_mode=None)
