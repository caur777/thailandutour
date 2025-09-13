# handlers/excursions/booking.py  (экскурсии)
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_CHAT
from utils.loader import load_excursions

router = Router()

class BookingStates(StatesGroup):
    waiting_name = State()
    waiting_count = State()
    waiting_date = State()
    waiting_residence = State()
    waiting_transport = State()     # Да/Нет с кнопками
    waiting_messenger = State()     # WhatsApp / Telegram (кнопки)
    waiting_phone = State()         # номер, привязанный к выбранному мессенджеру
    waiting_wishes = State()

def _get_title(cat_id: str, tour_id: str) -> str:
    data = load_excursions()
    categories = data.get("category", []) if isinstance(data, dict) else []
    cat = next((c for c in categories if c.get("id") == cat_id), None)
    if not cat:
        return tour_id
    tour = next((t for t in (cat.get("tour") or []) if t.get("id") == tour_id), None)
    return tour.get("title") if tour else tour_id

def _normalize_messenger(s: str) -> str | None:
    t = (s or "").strip().lower()
    if any(x in t for x in ("wa", "whatsapp", "ватсап", "ватсапп")):
        return "WhatsApp"
    if any(x in t for x in ("tg", "telegram", "телеграм", "телеграмм")):
        return "Telegram"
    return None

def _normalize_yes_no(s: str) -> str | None:
    t = (s or "").strip().lower()
    if t in ("да", "yes", "y", "д", "ага", "нужно", "надо"):
        return "Да"
    if t in ("нет", "no", "n", "не", "не нужно", "не надо"):
        return "Нет"
    return None

@router.callback_query(lambda cq: cq.data and (cq.data.startswith("book_exc:") or cq.data.startswith("book:")))
async def start_excursion_booking(query: CallbackQuery, state: FSMContext):
    # Поддерживаем оба префикса: book_exc: и book:
    parts = query.data.split(":")[1:]  # без префикса
    if len(parts) < 2:
        await query.answer("Некорректные параметры бронирования", show_alert=True)
        return
    cat_id, exc_id = parts[-2], parts[-1]

    await state.update_data(cat_id=cat_id, excursion_id=exc_id)
    await state.set_state(BookingStates.waiting_name)
    await query.message.answer("Ваше имя?")
    await query.answer()

@router.message(BookingStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=(message.text or "").strip())
    await message.answer("Сколько гостей всего (взрослых и детей)?")
    await state.set_state(BookingStates.waiting_count)

@router.message(BookingStates.waiting_count)
async def process_count(message: Message, state: FSMContext):
    await state.update_data(count=(message.text or "").strip())
    await message.answer("На какую дату хотите забронировать?")
    await state.set_state(BookingStates.waiting_date)

@router.message(BookingStates.waiting_date)
async def process_date(message: Message, state: FSMContext):
    await state.update_data(date=(message.text or "").strip())
    await message.answer("Где вы проживаете (отель/район)?")
    await state.set_state(BookingStates.waiting_residence)

@router.message(BookingStates.waiting_residence)
async def process_residence(message: Message, state: FSMContext):
    await state.update_data(residence=(message.text or "").strip())
    # Транспорт — кнопки Да/Нет
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Да", callback_data="book_transport:yes"),
        InlineKeyboardButton(text="Нет", callback_data="book_transport:no"),
    ]])
    await message.answer("Нужен транспорт?", reply_markup=kb)
    await state.set_state(BookingStates.waiting_transport)

# Транспорт — выбор кнопками
@router.callback_query(BookingStates.waiting_transport, F.data.startswith("book_transport:"))
async def transport_cb(query: CallbackQuery, state: FSMContext):
    code = query.data.split(":")[1]
    await state.update_data(transport="Да" if code == "yes" else "Нет")
    # Сразу переходим к мессенджеру
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="WhatsApp", callback_data="book_messenger:wa"),
        InlineKeyboardButton(text="Telegram", callback_data="book_messenger:tg"),
    ]])
    await query.message.answer("Где удобнее связаться?", reply_markup=kb)
    await state.set_state(BookingStates.waiting_messenger)
    await query.answer()

# Транспорт — фолбэк по тексту
@router.message(BookingStates.waiting_transport)
async def transport_msg(message: Message, state: FSMContext):
    ans = _normalize_yes_no(message.text)
    if not ans:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Да", callback_data="book_transport:yes"),
            InlineKeyboardButton(text="Нет", callback_data="book_transport:no"),
        ]])
        await message.answer("Пожалуйста, выберите кнопку: Да или Нет.", reply_markup=kb)
        return
    await state.update_data(transport=ans)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="WhatsApp", callback_data="book_messenger:wa"),
        InlineKeyboardButton(text="Telegram", callback_data="book_messenger:tg"),
    ]])
    await message.answer("Где удобнее связаться?", reply_markup=kb)
    await state.set_state(BookingStates.waiting_messenger)

# Мессенджер — выбор кнопками
@router.callback_query(BookingStates.waiting_messenger, F.data.startswith("book_messenger:"))
async def choose_messenger_cb(query: CallbackQuery, state: FSMContext):
    code = query.data.split(":")[1]
    messenger = "WhatsApp" if code == "wa" else "Telegram"
    await state.update_data(messenger=messenger)
    await query.message.answer("Оставьте номер телефона, привязанный к выбранному мессенджеру.")
    await state.set_state(BookingStates.waiting_phone)
    await query.answer()

# Мессенджер — фолбэк по тексту
@router.message(BookingStates.waiting_messenger)
async def choose_messenger_msg(message: Message, state: FSMContext):
    m = _normalize_messenger(message.text)
    if not m:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="WhatsApp", callback_data="book_messenger:wa"),
            InlineKeyboardButton(text="Telegram", callback_data="book_messenger:tg"),
        ]])
        await message.answer("Пожалуйста, выберите кнопку: WhatsApp или Telegram.", reply_markup=kb)
        return
    await state.update_data(messenger=m)
    await message.answer("Оставьте номер телефона, привязанный к выбранному мессенджеру")
    await state.set_state(BookingStates.waiting_phone)

@router.message(BookingStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    await state.update_data(phone=phone)
    await message.answer("Пожелания или вопросы? (после этого с вами свяжется менеджер)")
    await state.set_state(BookingStates.waiting_wishes)

@router.message(BookingStates.waiting_wishes)
async def process_wishes(message: Message, state: FSMContext):
    data = await state.get_data()
    wishes = (message.text or "").strip()
    await state.update_data(wishes=wishes)

    cat_id = data.get("cat_id")
    exc_id = data.get("excursion_id")
    title = _get_title(cat_id, exc_id)

    user = message.from_user
    contact = f"@{user.username}" if user.username else f"[клиент](tg://user?id={user.id})"

    text = (
        "✅ НОВАЯ ЗАЯВКА НА ЭКСКУРСИЮ ✉️\n"
        f"*Экскурсия:* {title}\n"
        f"*Имя:* {data.get('name')}\n"
        f"*Гости:* {data.get('count')}\n"
        f"*Дата:* {data.get('date')}\n"
        f"*Проживание:* {data.get('residence')}\n"
        f"*Транспорт:* {data.get('transport')}\n"
        f"*Мессенджер:* {data.get('messenger')}\n"
        f"*Телефон:* {data.get('phone')}\n"
        f"*Пожелания:* {wishes}\n"
        f"*Контакт клиента:* {contact}"
    )

    await message.bot.send_message(chat_id=ADMIN_CHAT, text=text, parse_mode="Markdown")

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к экскурсии", callback_data=f"details:{cat_id}:{exc_id}")]
    ])
    await message.answer("Спасибо! Запрос отправлен. Менеджер свяжется с вами.", reply_markup=markup)

    await state.clear()
