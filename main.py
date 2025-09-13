import os

# Пытаемся взять TELEGRAM_TOKEN из переменной окружения (для Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Если переменной нет (локальный запуск) → берём из config_local.py
if TELEGRAM_TOKEN is None:
    try:
        from config_local import TELEGRAM_TOKEN
        print("✅ Используем локальный TELEGRAM_TOKEN из config_local.py")
    except ImportError:
        raise Exception("❌ TELEGRAM_TOKEN не найден. Добавь его в config_local.py или в переменные окружения.")

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F


# Common
from handlers.common.common import router as common_router

# Excursions
from handlers.excursions.catalog import catalog_router
from handlers.excursions.important import important_router
from handlers.excursions.categories import categories_router
from handlers.excursions.details import details_router
from handlers.excursions.pricing import router as excursions_pricing_router
from handlers.excursions.booking import router as booking_router
from handlers.excursions.list import router as excursions_list_router
from handlers.excursions.gallery import router as gallery_router
from handlers.excursions.info import router as info_router




logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


dp.include_routers(
    common_router,
    catalog_router,
    important_router,
    categories_router,
    details_router,
    excursions_pricing_router,
    booking_router,
    excursions_list_router,
    gallery_router,
    info_router
    )

async def main():
    logging.info("🚀 Запуск Utour Bot")
    await dp.start_polling(bot) 

if __name__ == "__main__":
    asyncio.run(main())
