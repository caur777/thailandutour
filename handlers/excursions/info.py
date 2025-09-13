from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

router = Router()

@router.callback_query(lambda cq: cq.data and cq.data.startswith("info:"))
async def show_excursion_info(query: CallbackQuery):
    parts = query.data.split(":")[1:]
    *category_ids, exc_id = parts

    info_path = os.path.join("data", "excursions", *category_ids, exc_id, "info.md")
    if not os.path.exists(info_path):
        await query.answer("Файл информации не найден", show_alert=True)
        return

    with open(info_path, "r", encoding="utf-8") as f:
        text = f.read()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data=f"details:{':'.join(category_ids)}:{exc_id}")
    builder.adjust(1)

    await query.message.delete()
    await query.message.answer(
        text=text,
        reply_markup=builder.as_markup()
    )

    await query.answer()
