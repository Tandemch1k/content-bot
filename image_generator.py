"""
image_generator.py — профессиональные фото через Pexels API
Бесплатно, высокое качество, поиск по теме
"""

import httpx
import os
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Поисковые запросы по типу поста
SEARCH_QUERIES = {
    "news": [
        "Dubai skyline",
        "Dubai Marina luxury",
        "Dubai Downtown",
        "Dubai real estate",
        "UAE luxury property",
        "Dubai architecture modern",
    ],
    "tip": [
        "luxury apartment interior",
        "modern living room",
        "luxury penthouse",
        "Dubai villa pool",
        "luxury bedroom interior",
        "modern kitchen luxury",
    ],
    "insight": [
        "Dubai aerial view",
        "Palm Jumeirah",
        "Dubai cityscape",
        "UAE construction",
        "Dubai business district",
        "Dubai waterfront",
    ],
}

# По ключевым словам в теме
KEYWORD_QUERIES = {
    "marina": "Dubai Marina",
    "palm": "Palm Jumeirah Dubai",
    "downtown": "Downtown Dubai",
    "jbr": "Jumeirah Beach Dubai",
    "business bay": "Business Bay Dubai",
    "creek": "Dubai Creek",
    "villa": "luxury villa pool",
    "apartment": "luxury apartment interior",
    "off-plan": "construction Dubai",
    "golden visa": "Dubai luxury lifestyle",
    "invest": "Dubai investment",
    "аренда": "luxury rental apartment",
    "studio": "studio apartment modern",
    "penthouse": "penthouse luxury view",
}

# Fallback фото высокого качества
FALLBACK_URLS = {
    "news": [
        "https://images.pexels.com/photos/1105766/pexels-photo-1105766.jpeg?w=1280&q=90",
        "https://images.pexels.com/photos/2044434/pexels-photo-2044434.jpeg?w=1280&q=90",
        "https://images.pexels.com/photos/3989837/pexels-photo-3989837.jpeg?w=1280&q=90",
    ],
    "tip": [
        "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?w=1280&q=90",
        "https://images.pexels.com/photos/1648776/pexels-photo-1648776.jpeg?w=1280&q=90",
        "https://images.pexels.com/photos/2251247/pexels-photo-2251247.jpeg?w=1280&q=90",
    ],
    "insight": [
        "https://images.pexels.com/photos/2760209/pexels-photo-2760209.jpeg?w=1280&q=90",
        "https://images.pexels.com/photos/1486785/pexels-photo-1486785.jpeg?w=1280&q=90",
        "https://images.pexels.com/photos/2096578/pexels-photo-2096578.jpeg?w=1280&q=90",
    ],
}


def _find_keyword_query(text: str) -> Optional[str]:
    text_lower = text.lower()
    for keyword, query in KEYWORD_QUERIES.items():
        if keyword in text_lower:
            return query
    return None


def fetch_pexels_photo(query: str) -> Optional[str]:
    """Ищет фото на Pexels и возвращает URL."""
    if not PEXELS_API_KEY:
        logger.warning("PEXELS_API_KEY not set")
        return None
    try:
        resp = httpx.get(
            "https://api.pexels.com/v1/search",
            params={
                "query": query,
                "orientation": "landscape",
                "size": "large",
                "per_page": 15,
            },
            headers={"Authorization": PEXELS_API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            photos = data.get("photos", [])
            if photos:
                photo = random.choice(photos[:15])
                url = photo.get("src", {}).get("large2x", "")
                if not url:
                    url = photo.get("src", {}).get("large", "")
                if url:
                    logger.info(f"Pexels photo found for: {query}")
                    return url
        else:
            logger.warning(f"Pexels API status {resp.status_code}")
    except Exception as e:
        logger.error(f"Pexels error: {e}")
    return None


def get_image(post_type: str, topic_hint: str = "") -> str:
    """Подбирает профессиональное фото по теме поста."""
    # По ключевым словам темы
    if topic_hint:
        kw_query = _find_keyword_query(topic_hint)
        if kw_query:
            url = fetch_pexels_photo(kw_query)
            if url:
                return url

    # По типу поста
    queries = SEARCH_QUERIES.get(post_type, SEARCH_QUERIES["news"])
    query = random.choice(queries)
    url = fetch_pexels_photo(query)
    if url:
        return url

    # Fallback
    logger.info(f"Using fallback for '{post_type}'")
    fallbacks = FALLBACK_URLS.get(post_type, FALLBACK_URLS["news"])
    return random.choice(fallbacks)
