# handlers/excursions/pricing.py

from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.loader import load_excursions

import os

router = Router()

@router.callback_query(lambda cq: cq.data and cq.data.startswith("price:"))
async def show_excursion_price(query: CallbackQuery):
    parts = query.data.split(":")[1:]
    *category_ids, exc_id = parts

    categories = load_excursions()
    node = None
    for cid in category_ids:
        node = next((c for c in categories if c['id'] == cid), None)
        if not node:
            await query.answer("Категория не найдена", show_alert=True)
            return
        categories = node.get('subcategories', [])

    excursions = node.get('excursions', [])
    excursion = next((e for e in excursions if e['id'] == exc_id), None)
    if not excursion:
        await query.answer("Экскурсия не найдена", show_alert=True)
        return

    # Новый путь к файлу prices.md
    md_path = os.path.join("data", "excursions", *category_ids, exc_id, "prices.md")

    if not os.path.exists(md_path):
        await query.answer("Файл с ценами не найден", show_alert=True)
        return

    with open(md_path, "r", encoding="utf-8") as f:
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
