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

# YouTube каналы по Dubai real estate (channel ID для RSS)
YOUTUBE_CHANNELS = {
    "Farooq Syed": "UCzRjFuKfBgLEAQ2gxDWSiYA",
    "Dubai Property": "UC_7VNNkk9bGXH7bJwWFNvEQ",
    "Property Finder": "UCf5nRHUb5HdL1qAtGPnXeNg",
    "Metropolitan Premium": "UCKQfxhPz6YxL9dAznAQl9gQ",
}

# Reddit — открытые сабреддиты
REDDIT_SUBS = [
    "DubaiRealEstate",
    "dubai",
    "UAEfinance",
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


def fetch_youtube_news() -> List[Dict]:
    """Получает новые видео с YouTube каналов по недвижимости Dubai через RSS."""
    articles = []
    for channel_name, channel_id in YOUTUBE_CHANNELS.items():
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = entry.get("title", "")
                if not title:
                    continue
                summary = entry.get("summary", "") or entry.get("media_description", "")
                articles.append({
                    "title": f"[YouTube] {title}",
                    "summary": summary[:300],
                    "url": entry.get("link", ""),
                    "source": f"YouTube: {channel_name}",
                    "published": str(entry.get("published_parsed", "")),
                })
        except Exception as e:
            logger.warning(f"YouTube RSS error for {channel_name}: {e}")
    logger.info(f"Fetched {len(articles)} YouTube videos")
    return articles


def fetch_reddit_posts() -> List[Dict]:
    """Получает топ посты с Reddit по Dubai недвижимости."""
    articles = []
    headers = {"User-Agent": "DubaiRealEstateBot/1.0"}
    for sub in REDDIT_SUBS:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
            resp = httpx.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                p = post.get("data", {})
                title = p.get("title", "")
                if not title:
                    continue
                # Фильтр по ключевым словам
                if not any(kw in title.lower() for kw in KEYWORDS):
                    continue
                score = p.get("score", 0)
                comments = p.get("num_comments", 0)
                articles.append({
                    "title": f"[Reddit r/{sub}] {title}",
                    "summary": p.get("selftext", "")[:300],
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "source": f"Reddit r/{sub} (👍{score} 💬{comments})",
                    "published": "",
                })
        except Exception as e:
            logger.warning(f"Reddit error for r/{sub}: {e}")
    logger.info(f"Fetched {len(articles)} Reddit posts")
    return articles


def get_all_news() -> List[Dict]:
    """Объединяет все источники, убирает дубли."""
    articles = fetch_rss_news() + fetch_google_news() + fetch_youtube_news() + fetch_reddit_posts()

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
