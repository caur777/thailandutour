# utils/md_loader.py
from pathlib import Path

def load_md_file(category: str, yacht_id: str, filename: str) -> str:
    path = Path(f"data/yachts/info/{category}/{yacht_id}/{filename}")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Информация отсутствует."
