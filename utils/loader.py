# utils/loader.py
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


# Базовый путь к папке data (можно переопределить переменной окружения UTOUR_DATA_DIR)
_data_root_env = os.getenv("UTOUR_DATA_DIR")
DATA_DIR: Path = Path(_data_root_env).resolve() if _data_root_env else (Path(__file__).parent.parent / "data").resolve()


def _section_path(section: str) -> Path:
    """
    Возвращает абсолютный путь к файлу data/<section>/<section>.json
    """
    return (DATA_DIR / section / f"{section}.json").resolve()


@lru_cache(maxsize=16)
def load_json(section: str) -> Dict[str, Any]:
    """
    Загружает и возвращает содержимое JSON-файла для заданного раздела.

    :param section: имя подпапки и файла <section>.json внутри data/
    :raises FileNotFoundError: если файл отсутствует
    :raises ValueError: если JSON повреждён
    """
    path = _section_path(section)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON в {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"Некорректный формат в {path}: ожидается объект JSON (dict)")
    return data


def clear_cache() -> None:
    """Сбрасывает кэш загрузки JSON (если правили файлы на диске во время работы бота)."""
    load_json.cache_clear()  # type: ignore[attr-defined]


# ===== EXCURSIONS (НОВЫЙ формат) =====

def load_excursions() -> Dict[str, Any]:
    """
    Возвращает ПОЛНЫЙ JSON каталога экскурсий (data/excursions/excursions.json).

    НОВЫЙ формат использует ключи:
      - "category": список категорий
      - внутри каждой категории: "tour": список туров
    """
    return load_json("excursions")


def load_excursion_categories() -> List[Dict[str, Any]]:
    """Возвращает список категорий экскурсий (ключ 'category')."""
    data = load_excursions()
    categories = data.get("category", [])
    return categories if isinstance(categories, list) else []


def get_category_by_id(category_id: str) -> Optional[Dict[str, Any]]:
    """Ищет категорию по id в excursions.json."""
    for c in load_excursion_categories():
        if isinstance(c, dict) and c.get("id") == category_id:
            return c
    return None


def get_tours_by_category_id(category_id: str) -> List[Dict[str, Any]]:
    """Возвращает список туров внутри категории по её id (ключ 'tour')."""
    cat = get_category_by_id(category_id)
    tours = (cat or {}).get("tour", [])
    return tours if isinstance(tours, list) else []

