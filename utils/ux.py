# utils/ux.py
from __future__ import annotations
import asyncio
from typing import Optional, Iterable
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, FSInputFile, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

# Глобальные "замки" по чатам, чтобы не было гонок при двойных кликах
_CHAT_LOCKS: dict[int, asyncio.Lock] = {}

def _get_lock(chat_id: int) -> asyncio.Lock:
    lock = _CHAT_LOCKS.get(chat_id)
    if lock is None:
        lock = asyncio.Lock()
        _CHAT_LOCKS[chat_id] = lock
    return lock

def _chunks(text: str, limit: int = 4096) -> Iterable[str]:
    # Разумное разбиение длинных сообщений по абзацам
    if len(text) <= limit:
        yield text
        return
    buf = []
    size = 0
    for line in text.splitlines(keepends=True):
        if size + len(line) > limit and buf:
            yield "".join(buf)
            buf, size = [], 0
        buf.append(line)
        size += len(line)
    if buf:
        yield "".join(buf)

async def _safe_delete_message(cb: CallbackQuery, mid: int) -> None:
    try:
        await cb.bot.delete_message(cb.message.chat.id, mid)
    except TelegramBadRequest:
        # уже удалено/слишком старо/не наше сообщение — игнорируем
        pass

async def _ack(cb: CallbackQuery, text: Optional[str] = None) -> None:
    # Быстро подтверждаем callback (до 10с у Telegram)
    try:
        await cb.answer(text=text) if text else await cb.answer()
    except TelegramBadRequest:
        pass

async def _set_last_mid(state: FSMContext, mid: int) -> None:
    data = await state.get_data()
    data["last_mid"] = mid
    await state.set_data(data)

async def _pop_last_mid(state: FSMContext) -> Optional[int]:
    data = await state.get_data()
    last_mid = data.get("last_mid")
    # Не стираем, чтобы в следующий раз тоже удалить, но можно и pop
    return last_mid

async def show_screen_text(
    cb: CallbackQuery,
    state: FSMContext,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "HTML",
    ack_text: Optional[str] = None,
) -> list[Message]:
    """Удаляет прошлый экран бота, удаляет сообщение-кнопку, шлёт новый текст."""
    await _ack(cb, ack_text)
    chat_id = cb.message.chat.id
    lock = _get_lock(chat_id)
    async with lock:
        # удаляем прошлый экран бота (если был)
        last_mid = await _pop_last_mid(state)
        if last_mid:
            await _safe_delete_message(cb, last_mid)
        # удаляем сообщение, по которому кликнули (если это ботское)
        if cb.message and cb.message.from_user and cb.message.from_user.is_bot:
            await _safe_delete_message(cb, cb.message.message_id)
        # отправляем новый экран (поддержка длинных сообщений)
        sent_messages: list[Message] = []
        for i, chunk in enumerate(_chunks(text)):
            m = await cb.bot.send_message(
                chat_id, chunk,
                reply_markup=(reply_markup if i == 0 else None),
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
            sent_messages.append(m)
        if sent_messages:
            await _set_last_mid(state, sent_messages[0].message_id)
        return sent_messages

async def show_screen_photo(
    cb: CallbackQuery,
    state: FSMContext,
    photo: FSInputFile,
    caption: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "HTML",
    ack_text: Optional[str] = None,
) -> Message:
    """То же, но с фото-экраном (например, обложка каталога)."""
    await _ack(cb, ack_text)
    chat_id = cb.message.chat.id
    lock = _get_lock(chat_id)
    async with lock:
        last_mid = await _pop_last_mid(state)
        if last_mid:
            await _safe_delete_message(cb, last_mid)
        if cb.message and cb.message.from_user and cb.message.from_user.is_bot:
            await _safe_delete_message(cb, cb.message.message_id)
        m = await cb.bot.send_photo(
            chat_id, photo=photo, caption=caption,
            reply_markup=reply_markup, parse_mode=parse_mode,
        )
        await _set_last_mid(state, m.message_id)
        return m
