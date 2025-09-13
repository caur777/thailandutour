# config.py
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Куда отправлять заявки менеджеру (chat_id или @username)
ADMIN_CHAT = "7904854267"        # или числовой chat_id

# Для кнопки «Связаться с менеджером» в меню
MANAGER_USERNAME = "utourthailand"  # без @