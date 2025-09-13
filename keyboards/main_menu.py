from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню бота
main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏝️ Каталог экскурсий Пхукета", callback_data="show_catalog")],
    [InlineKeyboardButton(text="📣 Канал U TOUR", url="https://t.me/thailandutour")],
    [InlineKeyboardButton(text="⭐️ Почитать отзывы", url="https://t.me/thailandutour_reviews")],
    [InlineKeyboardButton(text="💬 Связаться с менеджером", url="https://t.me/utourthailand")],
])
