"""
threads_publisher.py — публикация в Threads через Meta Graph API
Требует: THREADS_USER_ID, THREADS_ACCESS_TOKEN
"""

import httpx
import os
import logging

logger = logging.getLogger(__name__)

THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")
THREADS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
BASE_URL = "https://graph.threads.net/v1.0"


def publish_to_threads(text: str) -> bool:
    """
    Публикует текстовый пост в Threads.
    Возвращает True если успешно.
    """
    if not THREADS_USER_ID or not THREADS_TOKEN:
        logger.warning("Threads credentials not set — skipping")
        return False

    try:
        # Шаг 1: Создать медиа-контейнер
        create_resp = httpx.post(
            f"{BASE_URL}/{THREADS_USER_ID}/threads",
            params={
                "media_type": "TEXT",
                "text": text,
                "access_token": THREADS_TOKEN,
            },
            timeout=30,
        )
        create_resp.raise_for_status()
        container_id = create_resp.json().get("id")

        if not container_id:
            logger.error("No container_id from Threads API")
            return False

        # Шаг 2: Опубликовать контейнер
        publish_resp = httpx.post(
            f"{BASE_URL}/{THREADS_USER_ID}/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": THREADS_TOKEN,
            },
            timeout=30,
        )
        publish_resp.raise_for_status()
        post_id = publish_resp.json().get("id")
        logger.info(f"Published to Threads: {post_id}")
        return True

    except Exception as e:
        logger.error(f"Threads publish error: {e}")
        return False
