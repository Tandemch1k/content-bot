"""
image_generator.py — AI генерация изображений через fal.ai + FLUX
Реалистичные фото под каждый пост
"""

import httpx
import os
import random
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

FAL_API_KEY = os.environ.get("FAL_API_KEY", "")

# Стиль для всех изображений
BASE_STYLE = (
    "Photorealistic, ultra detailed, 8K resolution, "
    "magazine quality, sharp crisp details, "
    "no people, no text, no watermarks, no logo"
)

# Разные стили съёмки для разнообразия
PHOTO_STYLES = [
    "aerial drone photography, bird eye view",
    "golden hour sunset photography",
    "blue hour night photography, city lights",
    "bright daylight photography, clear sky",
    "interior architectural photography",
    "exterior architectural photography",
    "panoramic wide angle photography",
]

# Негативный промпт
NEGATIVE_PROMPT = (
    "cartoon, illustration, watermark, text, logo, "
    "blurry, low quality, dark, ugly, distorted, "
    "people, faces, crowds"
)

# Fallback Pexels фото высокого качества
FALLBACK_URLS = {
    "news": [
        "https://images.pexels.com/photos/1105766/pexels-photo-1105766.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/2044434/pexels-photo-2044434.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/3989837/pexels-photo-3989837.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/1486785/pexels-photo-1486785.jpeg?auto=compress&w=1280",
    ],
    "tip": [
        "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/1648776/pexels-photo-1648776.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/2251247/pexels-photo-2251247.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/276724/pexels-photo-276724.jpeg?auto=compress&w=1280",
    ],
    "insight": [
        "https://images.pexels.com/photos/2760209/pexels-photo-2760209.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/460672/pexels-photo-460672.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/2096578/pexels-photo-2096578.jpeg?auto=compress&w=1280",
        "https://images.pexels.com/photos/449975/pexels-photo-449975.jpeg?auto=compress&w=1280",
    ],
}


def generate_fal_image(image_prompt: str) -> Optional[str]:
    """
    Генерирует изображение через fal.ai FLUX.
    Возвращает URL готового изображения.
    """
    if not FAL_API_KEY:
        logger.warning("FAL_API_KEY not set")
        return None

    # Выбираем случайный стиль съёмки для разнообразия
    photo_style = random.choice(PHOTO_STYLES)
    full_prompt = f"{image_prompt}. {photo_style}. {BASE_STYLE}"

    try:
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json",
        }

        # Запускаем генерацию через FLUX Dev (высокое качество)
        resp = httpx.post(
            "https://fal.run/fal-ai/flux/dev",
            headers=headers,
            json={
                "prompt": full_prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "image_size": "landscape_16_9",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "num_images": 1,
                "enable_safety_checker": True,
            },
            timeout=120,
        )

        if resp.status_code == 200:
            data = resp.json()
            images = data.get("images", [])
            if images:
                url = images[0].get("url", "")
                if url:
                    logger.info(f"fal.ai image generated successfully")
                    return url
        else:
            logger.error(f"fal.ai error {resp.status_code}: {resp.text[:200]}")

    except Exception as e:
        logger.error(f"fal.ai generation error: {e}")

    return None


def get_image(post_type: str, topic_hint: str = "") -> str:
    """
    Генерирует AI изображение через fal.ai.
    Fallback — Pexels фото если fal.ai недоступен.
    """
    if topic_hint and FAL_API_KEY:
        url = generate_fal_image(topic_hint)
        if url:
            return url

    # Fallback
    logger.info(f"Using Pexels fallback for '{post_type}'")
    fallbacks = FALLBACK_URLS.get(post_type, FALLBACK_URLS["news"])
    return random.choice(fallbacks)
