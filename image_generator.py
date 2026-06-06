"""
image_generator.py — подбор фото через Unsplash API по теме поста
Бесплатно: 50 запросов/час
"""

import httpx
import os
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# Поисковые запросы по типу поста и теме
SEARCH_QUERIES = {
    "news": [
        "Dubai skyline architecture",
        "Dubai Marina luxury",
        "Dubai Downtown skyscraper",
        "Dubai real estate modern",
        "UAE property luxury",
    ],
    "tip": [
        "Dubai apartment interior luxury",
        "Dubai villa pool",
        "luxury penthouse interior",
        "modern apartment Dubai",
        "Dubai property investment",
    ],
    "insight": [
        "Dubai aerial view",
        "Palm Jumeirah aerial",
        "Dubai city panorama",
        "Dubai construction development",
        "UAE real estate market",
    ],
}

# Запросы по ключевым словам в тексте
KEYWORD_QUERIES = {
    "marina": "Dubai Marina waterfront",
    "palm": "Palm Jumeirah Dubai",
    "downtown": "Downtown Dubai Burj Khalifa",
    "jbr": "JBR Jumeirah Beach Residence",
    "business bay": "Business Bay Dubai canal",
    "creek": "Dubai Creek Harbour",
    "villa": "Dubai villa luxury pool",
    "apartment": "Dubai luxury apartment interior",
    "off-plan": "Dubai construction skyscraper",
    "инвест": "Dubai investment property",
    "аренда": "Dubai rental apartment",
    "golden visa": "Dubai luxury lifestyle",
}

# Fallback фото если API не доступен
FALLBACK_URLS = {
    "news": [
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1080&q=80",
        "https://images.unsplash.com/photo-1582672750128-72a8e51cecd6?w=1080&q=80",
        "https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?w=1080&q=80",
    ],
    "tip": [
        "https://images.unsplash.com/photo-1582407947304-fd86f28f2f88?w=1080&q=80",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1080&q=80",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1080&q=80",
    ],
    "insight": [
        "https://images.unsplash.com/photo-1565019011521-b0575cbb57c6?w=1080&q=80",
        "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=1080&q=80",
        "https://images.unsplash.com/photo-1559329255-7c5e1b458e44?w=1080&q=80",
    ],
}


def _find_keyword_query(text: str) -> Optional[str]:
    """Ищет ключевые слова в тексте и возвращает подходящий запрос."""
    text_lower = text.lower()
    for keyword, query in KEYWORD_QUERIES.items():
        if keyword in text_lower:
            return query
    return None


def fetch_unsplash_photo(query: str) -> Optional[str]:
    """Получает случайное фото с Unsplash по запросу."""
    if not UNSPLASH_ACCESS_KEY:
        return None
    try:
        resp = httpx.get(
            "https://api.unsplash.com/photos/random",
            params={
                "query": query,
                "orientation": "landscape",
                "content_filter": "high",
            },
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            url = data.get("urls", {}).get("regular", "")
            if url:
                logger.info(f"Unsplash photo fetched for query: {query}")
                return url
    except Exception as e:
        logger.warning(f"Unsplash API error: {e}")
    return None


def get_image(post_type: str, topic_hint: str = "") -> str:
    """
    Подбирает фото по теме поста.
    1. Ищет ключевые слова в теме
    2. Использует тип поста
    3. Fallback — статичные URL
    """
    # Пробуем найти по ключевым словам в теме
    if topic_hint:
        kw_query = _find_keyword_query(topic_hint)
        if kw_query:
            url = fetch_unsplash_photo(kw_query)
            if url:
                return url

    # Берём случайный запрос по типу поста
    queries = SEARCH_QUERIES.get(post_type, SEARCH_QUERIES["news"])
    query = random.choice(queries)
    url = fetch_unsplash_photo(query)
    if url:
        return url

    # Fallback — статичные красивые фото
    logger.info(f"Using static fallback for post type '{post_type}'")
    fallbacks = FALLBACK_URLS.get(post_type, FALLBACK_URLS["news"])
    return random.choice(fallbacks)
