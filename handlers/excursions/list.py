# Новый handlers/excursions/categories.py
from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from utils.loader import load_excursions
from config import MANAGER_USERNAME

router = Router()

@router.callback_query(lambda cq: cq.data and cq.data.startswith("category:"))
async def handle_category_callback(query: CallbackQuery):
    path_ids = query.data.split(":")[1:]
    categories = load_excursions()
    node = None
    for cid in path_ids:
        node = next((c for c in categories if c['id'] == cid), None)
        if not node:
            await query.answer("Категория не найдена", show_alert=True)
            return
        categories = node.get('subcategories', [])

    if node.get('subcategories'):
        builder = InlineKeyboardBuilder()
        for sub in node['subcategories']:
            cb = 'category:' + ':'.join(path_ids + [sub['id']])
            builder.button(text=sub['title'], callback_data=cb)
        back_cb = (
            'category:' + ':'.join(path_ids[:-1]) if len(path_ids) > 1 else 'show_catalog'
        )
        builder.button(text='🔙 Назад', callback_data=back_cb)
        builder.adjust(1)
        try:
            await query.message.edit_text("Выберите подкатегорию:", reply_markup=builder.as_markup())
        except TelegramBadRequest:
            pass
    else:
        excursions = node.get('excursions', [])
        if not excursions:
            await query.answer("Экскурсии не найдены", show_alert=True)
            return
        builder = InlineKeyboardBuilder()
        for exc in excursions:
            cb = 'details:' + ':'.join(path_ids + [exc['id']])
            builder.button(text=exc['title'], callback_data=cb)
        parent_cb = (
            'category:' + ':'.join(path_ids[:-1]) if len(path_ids) > 1 else 'show_catalog'
        )
        builder.button(text='🔙 Назад', callback_data=parent_cb)
        builder.adjust(1)
        try:
            await query.message.edit_text("\U0001F4DA Выберите экскурсию:", reply_markup=builder.as_markup())
        except TelegramBadRequest:
            pass

    await query.answer()

@router.callback_query(lambda cq: cq.data and cq.data.startswith("excursions:"))
async def show_excursions_list(query: CallbackQuery):
    parts = query.data.split(":")[1:]  # category_ids
    categories = load_excursions()

    node = None
    for cid in parts:
        node = next((c for c in categories if c["id"] == cid), None)
        if not node:
            await query.answer("Категория не найдена", show_alert=True)
            return
        categories = node.get("subcategories", [])

    excursions = node.get("excursions", [])
    if not excursions:
        await query.answer("Нет экскурсий в этой категории", show_alert=True)
        return

    text = f"<b>{node['title']}</b>\nВыберите экскурсию:"
    builder = InlineKeyboardBuilder()
    for e in excursions:
        builder.button(
            text=e["title"],
            callback_data=f"details:{':'.join(parts)}:{e['id']}"
        )
    builder.button(text="🔙 Назад", callback_data="show_excursion_categories")
    builder.adjust(1)
    await query.message.delete()
    await query.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await query.answer()
