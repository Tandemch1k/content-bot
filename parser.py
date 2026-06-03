"""
parser.py — парсер новостей о недвижимости Dubai
Источники: RSS-ленты + открытые сайты
"""

import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# RSS-ленты — новостные и государственные источники UAE
RSS_FEEDS = [
    # Топ новостные UAE
    "https://www.khaleejtimes.com/rss/property",
    "https://www.arabianbusiness.com/rss/real_estate",
    "https://gulfnews.com/rss/property",
    "https://www.zawya.com/rss/real-estate",
    "https://www.thenationalnews.com/rss/business/property",
    "https://www.propertyfinder.ae/blog/feed/",
    # Аналитика и данные
    "https://rss.app/feeds/dubairealestate.xml",
    "https://www.bayut.com/mybayut/feed/",
]

# Google News запросы для разных углов
GOOGLE_NEWS_QUERIES = [
    "Dubai real estate 2026",
    "Dubai property market news",
    "DLD Dubai Land Department transactions",
    "Dubai off-plan sales 2026",
    "UAE property investment 2026",
    "Emaar DAMAC Nakheel launch 2026",
]

# Ключевые слова для фильтрации
KEYWORDS = [
    "dubai", "дубай", "real estate", "property", "недвижимость",
    "apartment", "villa", "off-plan", "dld", "rera",
    "mortgage", "rent", "investment", "developer",
]


def fetch_rss_news(max_age_hours: int = 24) -> List[Dict]:
    """Собирает свежие новости из RSS-лент."""
    articles = []
    cutoff = datetime.now() - timedelta(hours=max_age_hours)

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                # Фильтр по дате
                published = entry.get("published_parsed")
                if published:
                    pub_date = datetime(*published[:6])
                    if pub_date < cutoff:
                        continue

                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "")

                # Фильтр по ключевым словам
                text = (title + " " + summary).lower()
                if not any(kw in text for kw in KEYWORDS):
                    continue

                articles.append({
                    "title": title,
                    "summary": _clean_html(summary)[:500],
                    "url": entry.get("link", ""),
                    "source": feed.feed.get("title", feed_url),
                    "published": str(published),
                })
        except Exception as e:
            logger.warning(f"RSS error {feed_url}: {e}")

    logger.info(f"Fetched {len(articles)} articles")
    return articles


def fetch_google_news() -> List[Dict]:
    """Гугл-новости по Dubai real estate через RSS — несколько запросов."""
    articles = []
    for query in GOOGLE_NEWS_QUERIES[:3]:  # Берём первые 3 запроса
        q = query.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={q}&hl=ru&gl=AE&ceid=AE:ru"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "")
                if not title:
                    continue
                articles.append({
                    "title": title,
                    "summary": entry.get("summary", "")[:300],
                    "url": entry.get("link", ""),
                    "source": f"Google News: {query}",
                    "published": str(entry.get("published_parsed", "")),
                })
        except Exception as e:
            logger.warning(f"Google News error for '{query}': {e}")
    return articles


def get_all_news() -> List[Dict]:
    """Объединяет все источники, убирает дубли."""
    articles = fetch_rss_news() + fetch_google_news()

    # Дедупликация по заголовку
    seen = set()
    unique = []
    for a in articles:
        key = a["title"][:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:20]  # Максимум 20 статей за раз


def _clean_html(text: str) -> str:
    """Убирает HTML теги."""
    try:
        return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()
    except Exception:
        return text
