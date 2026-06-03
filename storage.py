"""
storage.py — хранение очереди постов в JSON
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional

DATA_FILE = "posts.json"


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"queue": [], "published": [], "rejected": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_to_queue(posts: List[Dict]) -> List[str]:
    """Добавляет посты в очередь на одобрение. Возвращает список ID."""
    data = _load()
    ids = []
    for post in posts:
        post_id = str(uuid.uuid4())[:8]
        data["queue"].append({
            "id": post_id,
            "type": post.get("type"),
            "telegram_text": post.get("telegram_text"),
            "threads_text": post.get("threads_text"),
            "source_url": post.get("source_url", ""),
            "image_url": post.get("image_url", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "message_id": None,  # ID сообщения в Telegram для редактирования
        })
        ids.append(post_id)
    _save(data)
    return ids


def get_pending() -> List[Dict]:
    """Возвращает все посты ожидающие одобрения."""
    data = _load()
    return [p for p in data["queue"] if p["status"] == "pending"]


def get_post_by_id(post_id: str) -> Optional[Dict]:
    data = _load()
    for p in data["queue"]:
        if p["id"] == post_id:
            return p
    return None


def update_post_status(post_id: str, status: str, message_id: int = None):
    """Обновляет статус поста: approved / rejected / published."""
    data = _load()
    for p in data["queue"]:
        if p["id"] == post_id:
            p["status"] = status
            if message_id:
                p["message_id"] = message_id
            p["updated_at"] = datetime.now().isoformat()
            break
    _save(data)


def get_approved() -> List[Dict]:
    """Возвращает одобренные но ещё не опубликованные посты."""
    data = _load()
    return [p for p in data["queue"] if p["status"] == "approved"]


def mark_published(post_id: str):
    data = _load()
    for i, p in enumerate(data["queue"]):
        if p["id"] == post_id:
            p["status"] = "published"
            p["published_at"] = datetime.now().isoformat()
            data["published"].append(p)
            data["queue"].pop(i)
            break
    _save(data)


def update_post_text(post_id: str, platform: str, new_text: str):
    """Редактирование текста поста перед публикацией."""
    data = _load()
    for p in data["queue"]:
        if p["id"] == post_id:
            if platform == "telegram":
                p["telegram_text"] = new_text
            else:
                p["threads_text"] = new_text
            break
    _save(data)


def stats() -> Dict:
    data = _load()
    return {
        "pending": len([p for p in data["queue"] if p["status"] == "pending"]),
        "approved": len([p for p in data["queue"] if p["status"] == "approved"]),
        "published_today": len([
            p for p in data["published"]
            if p.get("published_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))
        ]),
        "total_published": len(data["published"]),
    }
