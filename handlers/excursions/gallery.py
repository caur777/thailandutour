# handlers/excursions/gallery.py
from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from pathlib import Path
import re

router = Router()

# Папка: data/excursions/<cat_id>/<tour_id>/gallery
BASE_DIR = Path(__file__).parent.parent.parent / "data" / "excursions"

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".jfif", ".heic", ".heif")
_num_re = re.compile(r"(\d+)")

# Состояние: отдельно по пользователю и конкретному туру
# ключ: f"{user_id}:{cat_id}:{tour_id}"
_user_idx: dict[str, int] = {}
_user_files: dict[str, list[Path]] = {}

def _key(user_id: int, cat_id: str, tour_id: str) -> str:
    return f"{user_id}:{cat_id}:{tour_id}"

def _gallery_dir(cat_id: str, tour_id: str) -> Path:
    return BASE_DIR / cat_id / tour_id / "gallery"

def _natural_key(p: Path):
    name = p.name
    return [int(s) if s.isdigit() else s.lower() for s in _num_re.split(name)]

def _collect_files(cat_id: str, tour_id: str) -> list[Path]:
    gal = _gallery_dir(cat_id, tour_id)
    if not gal.is_dir():
        return []
    files = [p for p in gal.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    files.sort(key=_natural_key)
    return files

async def _send_frame(query: CallbackQuery, user_id: int, cat_id: str, tour_id: str):
    key = _key(user_id, cat_id, tour_id)
    files = _user_files.get(key, [])
    if not files:
        await query.answer("Галерея пуста", show_alert=True)
        return

    idx = max(0, min(_user_idx.get(key, 0), len(files) - 1))
    _user_idx[key] = idx
    path = files[idx]

    caption = f"📷 Галерея\nФото {idx + 1} из {len(files)}\nЛистайте кнопками ниже."

    kb = InlineKeyboardBuilder()
    if idx > 0:
        kb.button(text="◀️ Назад", callback_data=f"gallery_prev:{cat_id}:{tour_id}")
    kb.button(text=f"{idx + 1}/{len(files)}", callback_data="noop")
    if idx < len(files) - 1:
        kb.button(text="Вперёд ▶️", callback_data=f"gallery_next:{cat_id}:{tour_id}")
    kb.button(text="🔙 Назад к экскурсии", callback_data=f"details:{cat_id}:{tour_id}")
    kb.adjust(3)

    # Чистим старое сообщение, чтобы не плодить ленту
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass

    file = FSInputFile(str(path))
    ext = path.suffix.lower()

    try:
        if ext == ".gif":
            await query.message.answer_animation(animation=file, caption=caption, reply_markup=kb.as_markup())
        else:
            await query.message.answer_photo(photo=file, caption=caption, reply_markup=kb.as_markup())
    except TelegramBadRequest:
        # Фолбэк для редких форматов: шлём как документ
        await query.message.answer_document(document=file, caption=caption, reply_markup=kb.as_markup())

    await query.answer()

# Открыть галерею
@router.callback_query(lambda cq: cq.data and cq.data.startswith("gallery:"))
async def gallery_open(query: CallbackQuery):
    # gallery:<cat_id>:<tour_id>
    _, cat_id, tour_id = query.data.split(":", 2)

    files = _collect_files(cat_id, tour_id)
    if not files:
        await query.answer("Фотографии не найдены", show_alert=True)
        return

    key = _key(query.from_user.id, cat_id, tour_id)
    _user_files[key] = files
    _user_idx[key] = 0

    await _send_frame(query, query.from_user.id, cat_id, tour_id)

# Листание вперёд
@router.callback_query(lambda cq: cq.data and cq.data.startswith("gallery_next:"))
async def gallery_next(query: CallbackQuery):
    _, cat_id, tour_id = query.data.split(":", 2)
    key = _key(query.from_user.id, cat_id, tour_id)
    if key in _user_idx:
        _user_idx[key] += 1
    await _send_frame(query, query.from_user.id, cat_id, tour_id)

# Листание назад
@router.callback_query(lambda cq: cq.data and cq.data.startswith("gallery_prev:"))
async def gallery_prev(query: CallbackQuery):
    _, cat_id, tour_id = query.data.split(":", 2)
    key = _key(query.from_user.id, cat_id, tour_id)
    if key in _user_idx:
        _user_idx[key] -= 1
    await _send_frame(query, query.from_user.id, cat_id, tour_id)
