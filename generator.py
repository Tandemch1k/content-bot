"""
generator.py — генерация контента через Claude AI
"""

import anthropic
import random
import logging
import os
from typing import List, Dict, Optional
from image_generator import get_image

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

CHANNEL_STYLE = """
Ты пишешь от лица Александра и Юлии — пара из России, живут и работают в Dubai 4 года в недвижимости. Личный Telegram-канал.

ГОЛОС: живой рассказ от первого лица. "я", "мы с Юлей", "наши клиенты", "за 4 года в Dubai я понял".

СТРУКТУРА — каждый раз разная, выбирай один из трёх:

А) Личная история:
[эмодзи] Цепляющий заголовок
"На прошлой неделе клиент спросил..." или "Расскажу историю..."
Конкретика: район, цифра, застройщик. Список выводов. Вопрос аудитории 👇

Б) Наблюдение эксперта:
[эмодзи] Заголовок-вопрос
"Мы с Юлей заметили..." или "За 4 года в Dubai я понял..."
2-3 абзаца. Совет в конце.

В) Горячая новость:
[эмодзи] Заголовок с цифрой
"Только что узнал..." или "Смотрю на рынок и вижу..."
Анализ + что это значит для читателей.

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:
- Эмодзи 8-12 штук ОБЯЗАТЕЛЬНО: 🏠🏗️🔑💰📈📊🌟⚡️🎯💡🔥✅❌🤔💬👇🏆💎🌍✈️📍🏖️🌆💸😎🤝🎉
- Ставь эмодзи в начале каждого абзаца и перед важными фактами
- Конкретика: Dubai Marina, JBR, Business Bay, Downtown, Palm Jumeirah, Creek Harbour
- Застройщики: Emaar, Damac, Nakheel, Sobha, Aldar
- СТРОГО до 650 символов — жёсткий лимит, не превышай никогда
- Максимум 3 абзаца
- БЕЗ хэштегов, БЕЗ горизонтальных линий, БЕЗ слова "Telegram:" в начале
- Пиши только текст поста, сразу с заголовка
"""

THREADS_STYLE = """
Ты — эксперт по недвижимости Dubai. Пишешь для Threads (короткий формат).
3-4 предложения. 1-2 эмодзи. Цепляющий инсайт. БЕЗ хэштегов.
"""

ALL_TOPICS = [
    "Dubai Marina в 2026 — стоит ли покупать или уже поздно?",
    "JBR vs Palm Jumeirah: где реально лучше жить и инвестировать",
    "Business Bay — недооценённый район или пузырь?",
    "Downtown Dubai: цены выросли на 40% — что дальше?",
    "Jumeirah Village Circle — лучший баланс цены и качества в 2026?",
    "Creek Harbour — ставка на будущее или риск?",
    "Dubai Hills vs Arabian Ranches: семейная недвижимость — где лучше?",
    "MBR City: новый центр Dubai или маркетинг?",
    "Как читать договор off-plan и не попасть в ловушку",
    "Payment plan 1%/месяц — выгода или скрытые риски?",
    "Топ-5 застройщиков Dubai которым можно доверять в 2026",
    "Как проверить застройщика за 15 минут — чеклист",
    "Off-plan assignment: заработать на перепродаже до сдачи",
    "Когда лучше покупать off-plan — на старте или перед сдачей?",
    "ROI 8-12% в Dubai — реально или маркетинговый трюк?",
    "Короткосрочная аренда (Airbnb) в Dubai: цифры и реальность",
    "Долгосрочная аренда vs Airbnb: что выгоднее в 2026?",
    "Топ-5 районов Dubai по доходности аренды в 2026",
    "Golden Visa через недвижимость — полный гайд 2026",
    "DLD fees, agency fee, NOC — все расходы при покупке",
    "Ипотека в Dubai для иностранцев: условия и реальность",
    "Freehold vs Leasehold — в чём разница и где покупать?",
    "Как открыть счёт в банке Dubai при покупке недвижимости",
    "Почему цены в Dubai не падают даже в кризис",
    "Экспаты бегут в Dubai: откуда едут и куда покупают",
    "Сезонность рынка Dubai — когда покупать выгоднее?",
    "Sustainable недвижимость в Dubai — тренд или необходимость?",
    "Рынок luxury в Dubai — кто покупает апартаменты за $5M+?",
    "10 вопросов которые нужно задать брокеру перед покупкой",
    "Как правильно торговаться при покупке недвижимости в Dubai",
    "Типичные ошибки русских при покупке недвижимости в Dubai",
    "Вторичный рынок vs первичный: что лучше в 2026?",
    "История клиента: купил студию за $150K — продал за $230K за 2 года",
    "Кейс: инвестор вложил $500K в 5 студий — считаем доход",
    "Как получить Golden Visa за 30 дней — реальная история",
    "Почему я продал квартиру в Москве и купил две в Dubai",
    "Как найти хорошего брокера в Dubai и не пожалеть",
    "Переезд в Dubai: что нужно сделать до покупки жилья",
    "Аренда vs покупка в Dubai: что выгоднее в 2026?",
    "DLD данные за месяц — что говорит официальная статистика",
    "Branded residences в Dubai: Versace, Bugatti, Armani — зачем?",
    "Инвестиции в парковку в Dubai — неочевидный способ заработать",
    "Как считать реальную доходность недвижимости в Dubai",
    "Damac Hills 2 — дальняя локация, стоит ли брать?",
    "Sobha Realty — почему этот застройщик растёт быстрее всех",
    "Palm Jumeirah — есть ли ещё смысл покупать в 2026?",
    "Что происходит с рынком аренды в Dubai прямо сейчас",
    "Crypto и недвижимость Dubai — как платить биткоином легально",
    "Как я помог клиенту сэкономить 200K AED при покупке",
    "5 вещей которые я бы сделал иначе при первой покупке в Dubai",
]


def _get_unused_topic() -> str:
    import json, os
    history_file = "topic_history.json"
    try:
        if os.path.exists(history_file):
            with open(history_file) as f:
                used = json.load(f)
        else:
            used = []
    except Exception:
        used = []

    available = [t for t in ALL_TOPICS if t not in used[-25:]]
    if not available:
        available = ALL_TOPICS

    topic = random.choice(available)
    used.append(topic)
    used = used[-35:]
    try:
        with open(history_file, 'w') as f:
            json.dump(used, f, ensure_ascii=False)
    except Exception:
        pass
    return topic


def generate_news_post(article: Dict, platform: str = "telegram") -> Optional[str]:
    style = CHANNEL_STYLE if platform == "telegram" else THREADS_STYLE
    prompt = f"""{style}

На основе этой новости напиши пост:
Заголовок: {article['title']}
Краткое содержание: {article['summary']}

Напиши только текст поста."""
    return _call_claude(prompt)


def generate_tip_post(platform: str = "telegram") -> Optional[str]:
    topic = _get_unused_topic()
    style = CHANNEL_STYLE if platform == "telegram" else THREADS_STYLE
    prompt = f"""{style}

Напиши экспертный пост на тему: «{topic}»

Пост должен быть практичным, с личным опытом и конкретными цифрами.
Напиши только текст поста."""
    return _call_claude(prompt)


def generate_insight_post(articles: List[Dict], platform: str = "telegram") -> Optional[str]:
    if not articles:
        return generate_tip_post(platform)
    news_digest = "\n".join([f"- {a['title']}" for a in articles[:5]])
    style = CHANNEL_STYLE if platform == "telegram" else THREADS_STYLE
    prompt = f"""{style}

На основе этих новостей напиши аналитический пост о трендах рынка Dubai:
{news_digest}

Напиши только текст поста."""
    return _call_claude(prompt)


def _generate_photo_query(text: str, post_type: str) -> str:
    prompt = f"""На основе этого текста поста о недвижимости Dubai создай промпт для AI генерации изображения.

Текст: {text[:400]}

Промпт на английском (10-20 слов). Выбирай разные типы сцен:
- Аэросъёмка: "Palm Jumeirah aerial view, turquoise water"
- Экстерьер: "Dubai Marina tower exterior, glass facade, blue sky"
- Панорама: "Downtown Dubai skyline, Burj Khalifa, night lights"
- Бассейн/терраса: "Infinity pool rooftop Dubai, city view"
- Пляж: "JBR beach Dubai, turquoise water, clear sky"
- Интерьер (редко): "Luxury Dubai penthouse living room"

Только промпт, без объяснений:"""
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"Photo query failed: {e}")
        defaults = {
            "news": "Dubai skyline luxury architecture golden hour",
            "tip": "Dubai Marina waterfront luxury buildings",
            "insight": "Palm Jumeirah aerial drone view",
        }
        return defaults.get(post_type, "Dubai real estate luxury")


def generate_batch(articles: List[Dict], count: int = 3) -> List[Dict]:
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
            else:
                tg = generate_insight_post(articles, "telegram")
                th = generate_insight_post(articles, "threads")
                source_url = ""

            if tg:
                photo_query = _generate_photo_query(tg, post_type)
                image_url = get_image(post_type, photo_query)
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
    if count <= 3:
        return ["news", "tip", "insight"][:count]
    elif count <= 5:
        return ["news", "tip", "news", "insight", "tip"][:count]
    else:
        return (["news", "tip", "news", "insight", "tip"] * 2)[:count]


def _call_claude(prompt: str) -> Optional[str]:
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Жёсткий лимит 650 символов
        if len(text) > 650:
            cut = text[:650]
            last_para = cut.rfind("\n\n")
            if last_para > 300:
                text = cut[:last_para].strip()
            else:
                last_sent = cut.rfind(".")
                if last_sent > 300:
                    text = cut[:last_sent + 1].strip()
                else:
                    text = cut.strip()
        return text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None
