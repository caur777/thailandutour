# handlers/excursions/details.py
from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from pathlib import Path
import logging

from utils.loader import get_category_by_id
from utils.ux import show_screen_text, show_screen_photo

details_router = Router()
TOURS_DIR = Path(__file__).parent.parent.parent / "data" / "excursions"

def _tour_dir(cat_id: str, tour_id: str) -> Path:
    return TOURS_DIR / cat_id / tour_id

def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception as e:
        logging.exception("Failed to read %s: %s", p, e)
        return ""

def _find_welcome_image(cat_id: str, tour_id: str) -> Path | None:
    base = _tour_dir(cat_id, tour_id)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = base / f"welcome{ext}"
        if p.exists():
            return p
    gal = base / "gallery"
    if gal.is_dir():
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            p = gal / f"cover{ext}"
            if p.exists():
                return p
        for p in sorted(gal.iterdir()):
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                return p
    return None

# ---- Проживание (Пхи-Пхи и Чео-Лан) ----------------------------------------

def _has_phi_accommodation(cat_id: str, tour_id: str) -> bool:
    # маркер: наличие файла с описанием
    return (_tour_dir(cat_id, tour_id) / "accommodation_phi.md").exists()

def _has_chl_accommodation(cat_id: str, tour_id: str) -> bool:
    # маркер: наличие файла с описанием озера Чео-Лан
    return (_tour_dir(cat_id, tour_id) / "accommodation_chl.md").exists()

def _menu_kb(cat_id: str, tour_id: str, *, add_phi_btn: bool = False):
    # Кнопки строим динамически, без заголовков/хэштегов в текстах
    kb = InlineKeyboardBuilder()

    # Кнопки проживаний (если есть файлы)
    has_phi = add_phi_btn or _has_phi_accommodation(cat_id, tour_id)
    has_chl = _has_chl_accommodation(cat_id, tour_id)
    if has_phi:
        kb.button(text="🏨 Проживание на Пхи-Пхи", callback_data=f"imp:phi:{cat_id}:{tour_id}")
    if has_chl:
        kb.button(text="🏞️ Проживание на Чео-Лан", callback_data=f"imp:chl:{cat_id}:{tour_id}")

    kb.button(text="🗺️ Описание и маршрут", callback_data=f"tour:info:{cat_id}:{tour_id}")
    kb.button(text="🖼️ Галерея", callback_data=f"gallery:{cat_id}:{tour_id}")
    kb.button(text="💰 Прайс", callback_data=f"tour:prices:{cat_id}:{tour_id}")
    kb.button(text="📲 Забронировать", callback_data=f"book_exc:{cat_id}:{tour_id}")
    kb.button(text="🔙 Назад к списку туров", callback_data=f"category:{cat_id}")
    kb.adjust(1)
    return kb.as_markup()

# ---- Экраны тура ------------------------------------------------------------

@details_router.callback_query(lambda cq: cq.data and cq.data.startswith("details:"))
async def show_tour_welcome(query: CallbackQuery, state: FSMContext):
    _, cat_id, tour_id = query.data.split(":", 2)

    category = get_category_by_id(cat_id)
    if not category or not isinstance(category.get("tour"), list):
        await show_screen_text(query, state, "Категория не найдена.")
        return

    tour = next((t for t in category["tour"] if isinstance(t, dict) and t.get("id") == tour_id), None)
    if not tour:
        await show_screen_text(query, state, "Тур не найден.", reply_markup=_menu_kb(cat_id, tour_id))
        return

    title = tour.get("title", "Тур")
    welcome_text = _read_text(_tour_dir(cat_id, tour_id) / "welcome.md")
    caption = (f"🏝️ <b>{title}</b>\n\n{welcome_text}").strip()

    img_path = _find_welcome_image(cat_id, tour_id)
    if img_path and img_path.exists():
        await show_screen_photo(
            query, state,
            photo=FSInputFile(str(img_path)),
            caption=caption,
            reply_markup=_menu_kb(cat_id, tour_id),
            parse_mode="HTML",
        )
    else:
        await show_screen_text(
            query, state,
            caption,
            reply_markup=_menu_kb(cat_id, tour_id),
            parse_mode="HTML",
        )

@details_router.callback_query(lambda cq: cq.data and cq.data.startswith("tour:"))
async def show_tour_section(query: CallbackQuery, state: FSMContext):
    # tour:<section>:<cat_id>:<tour_id>
    _, section, cat_id, tour_id = query.data.split(":", 3)

    if section == "info":
        text = _read_text(_tour_dir(cat_id, tour_id) / "info.md") or "Описание и маршрут появятся позже."
        await show_screen_text(query, state, text, reply_markup=_menu_kb(cat_id, tour_id), parse_mode=None)
        return

    if section == "prices":
        text = _read_text(_tour_dir(cat_id, tour_id) / "prices.md") or "Цены появятся позже."
        add_phi = _has_phi_accommodation(cat_id, tour_id)
        await show_screen_text(
            query, state, text,
            reply_markup=_menu_kb(cat_id, tour_id, add_phi_btn=add_phi),
            parse_mode=None
        )
        return

    # Галерея вынесена в handlers/excursions/gallery.py
