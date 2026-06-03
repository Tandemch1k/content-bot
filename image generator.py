"""
image_generator.py — генерация картинок через DALL-E 3
"""

import httpx
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Базовый стиль для всех картинок
IMAGE_STYLE = (
    "Photorealistic, luxury real estate photography, Dubai UAE. "
    "Professional architectural photography, golden hour lighting, "
    "high-end modern design, no text, no watermarks, no people."
)

# Промпты по типу поста
TYPE_PROMPTS = {
    "news": "Modern Dubai skyline with luxury residential towers, marina view, sunset",
    "tip": "Elegant interior of a luxury Dubai apartment, floor-to-ceiling windows, city view",
    "insight": "Aerial view of Dubai real estate development, Palm Jumeirah or Downtown Dubai",
}


def generate_image(post_type: str, topic_hint: str = "") -> Optional[str]:
    """
    Генерирует картинку через DALL-E 3.
    Возвращает URL изображения или None при ошибке.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set — skipping image generation")
        return None

    base_prompt = TYPE_PROMPTS.get(post_type, TYPE_PROMPTS["news"])

    # Если есть подсказка по теме — добавляем её
    if topic_hint:
        prompt = f"{base_prompt}. Context: {topic_hint[:100]}. {IMAGE_STYLE}"
    else:
        prompt = f"{base_prompt}. {IMAGE_STYLE}"

    try:
        response = httpx.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard",
            },
            timeout=60,
        )
        response.raise_for_status()
        image_url = response.json()["data"][0]["url"]
        logger.info(f"Generated image for post type '{post_type}'")
        return image_url

    except Exception as e:
        logger.error(f"DALL-E error: {e}")
        return None


def get_fallback_image(post_type: str) -> Optional[str]:
    """
    Fallback: бесплатное фото с Unsplash если DALL-E недоступен.
    Возвращает прямой URL картинки.
    """
    fallback_urls = {
        "news": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1024&q=80",
        "tip": "https://images.unsplash.com/photo-1582407947304-fd86f28f2f88?w=1024&q=80",
        "insight": "https://images.unsplash.com/photo-1565019011521-b0575cbb57c6?w=1024&q=80",
    }
    return fallback_urls.get(post_type, fallback_urls["news"])


def get_image(post_type: str, topic_hint: str = "") -> str:
    """
    Основная функция. Пробует DALL-E, при ошибке — Unsplash fallback.
    Всегда возвращает URL.
    """
    url = generate_image(post_type, topic_hint)
    if not url:
        logger.info(f"Using Unsplash fallback for post type '{post_type}'")
        url = get_fallback_image(post_type)
    return url
