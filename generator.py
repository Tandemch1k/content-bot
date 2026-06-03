"""
generator.py — генерация контента через Claude AI
Типы постов: новость, совет покупателю, инвест-аналитика
"""

import anthropic
import random
import logging
from typing import List, Dict, Optional
from image_generator import get_image

logger = logging.getLogger(__name__)

client = anthropic.Anthropic()

CHANNEL_STYLE = """
Ты — топ-эксперт по недвижимости Dubai. Пишешь для русскоязычного Telegram-канала.

СТРУКТУРА ПОСТА (строго соблюдай):
1. Цепляющий заголовок — жирным через **текст**, 1 строка, с эмодзи
2. Подзаголовок или вводная мысль — курсивом через _текст_, 1-2 строки
3. Пустая строка
4. Основной текст — 3-5 абзацев, каждый 2-3 предложения
5. Список с → или • если нужно перечисление
6. Пустая строка  
7. Вывод или призыв к действию — жирным

ПРАВИЛА:
- Только Markdown форматирование: **жирный**, _курсив_, `код`
- Конкретные цифры, районы, застройщики
- Живой разговорный тон, без канцелярита
- 200-400 слов
- 2-3 эмодзи максимум, только по делу
- БЕЗ хэштегов
- БЕЗ горизонтальных линий ---
"""

THREADS_STYLE = """
Ты — эксперт по недвижимости Dubai. Пишешь для Threads (короткий формат).

Стиль:
- Очень коротко: 3-5 предложений максимум
- Цепляющее начало
- Конкретный факт или инсайт
- 1-2 эмодзи
- НЕ используй хэштеги
"""

POST_TYPES = [
    "news",      # Новость с рынка
    "tip",       # Совет покупателю/инвестору
    "insight",   # Аналитика и тренды
]


def generate_news_post(article: Dict, platform: str = "telegram") -> Optional[str]:
    """Генерирует пост на основе новости."""
    style = CHANNEL_STYLE if platform == "telegram" else THREADS_STYLE

    prompt = f"""
{style}

На основе этой новости напиши пост:

Заголовок: {article['title']}
Краткое содержание: {article['summary']}
Источник: {article['source']}

Напиши только текст поста, без кавычек и пояснений.
"""
    return _call_claude(prompt)


def generate_tip_post(platform: str = "telegram") -> Optional[str]:
    """Генерирует полезный совет для покупателей/инвесторов."""
    topics = [
        "как выбрать район в Dubai для инвестиций в 2026 году",
        "на что обращать внимание при покупке off-plan в Dubai",
        "как работает процесс покупки недвижимости в Dubai для иностранцев",
        "ROI в разных районах Dubai — где выгоднее",
        "Golden Visa через недвижимость — условия и процесс",
        "разница между freehold и leasehold в Dubai",
        "как проверить застройщика в Dubai перед покупкой",
        "ошибки при покупке недвижимости в Dubai которые совершают русские",
        "DLD fees и другие расходы при покупке — полный расчёт",
        "аренда vs покупка в Dubai: что выгоднее в 2026",
    ]

    topic = random.choice(topics)
    style = CHANNEL_STYLE if platform == "telegram" else THREADS_STYLE

    prompt = f"""
{style}

Напиши экспертный пост на тему: «{topic}»

Пост должен быть практичным и полезным для русскоязычного покупателя или инвестора.
Напиши только текст поста, без кавычек и пояснений.
"""
    return _call_claude(prompt)


def generate_insight_post(articles: List[Dict], platform: str = "telegram") -> Optional[str]:
    """Генерирует аналитический пост на основе нескольких новостей."""
    if not articles:
        return generate_tip_post(platform)

    news_digest = "\n".join([
        f"- {a['title']}" for a in articles[:5]
    ])

    style = CHANNEL_STYLE if platform == "telegram" else THREADS_STYLE

    prompt = f"""
{style}

На основе этих новостей за последние дни напиши аналитический пост о трендах рынка недвижимости Dubai:

{news_digest}

Выдели главный тренд, объясни что это значит для покупателей и инвесторов.
Напиши только текст поста, без кавычек и пояснений.
"""
    return _call_claude(prompt)


def generate_batch(articles: List[Dict], count: int = 5) -> List[Dict]:
    """
    Генерирует пачку постов для одобрения.
    Возвращает список: [{type, telegram_text, threads_text, source_url}]
    """
    posts = []
    post_types = _plan_day(count)

    news_pool = articles.copy()

    for post_type in post_types:
        try:
            if post_type == "news" and news_pool:
                article = news_pool.pop(0)
                tg = generate_news_post(article, "telegram")
                th = generate_news_post(article, "threads")
                source_url = article.get("url", "")
            elif post_type == "tip":
                tg = generate_tip_post("telegram")
                th = generate_tip_post("threads")
                source_url = ""
            else:  # insight
                tg = generate_insight_post(articles, "telegram")
                th = generate_insight_post(articles, "threads")
                source_url = ""

            if tg:
                # Генерируем картинку
                topic_hint = article.get("title", "") if post_type == "news" and news_pool else ""
                image_url = get_image(post_type, topic_hint)

                posts.append({
                    "type": post_type,
                    "telegram_text": tg,
                    "threads_text": th or tg[:280],
                    "source_url": source_url,
                    "image_url": image_url,
                })
        except Exception as e:
            logger.error(f"Generation error for {post_type}: {e}")

    return posts


def _plan_day(count: int) -> List[str]:
    """Планирует микс типов постов на день."""
    if count <= 3:
        return ["news", "tip", "insight"][:count]
    elif count <= 5:
        return ["news", "tip", "news", "insight", "tip"][:count]
    else:
        base = ["news", "tip", "news", "insight", "tip"]
        return (base * 2)[:count]


def _call_claude(prompt: str) -> Optional[str]:
    """Вызывает Claude API."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None
