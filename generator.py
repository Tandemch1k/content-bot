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
Ты пишешь от лица Александра и Юлии — пары из России, живут и работают в Dubai 4 года в недвижимости. Личный Telegram-канал.

ГОЛОС:
- От первого лица: "я", "мы с Юлей", "наши клиенты", "я сам видел", "за 4 года в Dubai"
- Живой рассказ как другу — не статья, а личная история
- Иногда: "когда мы только приехали", "наш клиент на прошлой неделе", "был на этом объекте вчера"
- Экспертность через личный опыт, не сухие факты
- Юмор, честность, иногда провокация

СТРУКТУРА — каждый раз разная:

Вариант А (личная история):
🔥 **Заголовок — провокация или инсайт**
_Контекст одной строкой_
"На прошлой неделе клиент спросил меня..." или "Расскажу историю..."
Личный опыт + конкретика. Список с выводами. Вопрос 👇

Вариант Б (наблюдение эксперта):
💡 **Заголовок-вопрос**
"Мы с Юлей заметили..." или "За 4 года в Dubai я понял..."
2-3 абзаца. Личный совет курсивом в конце.

Вариант В (горячая новость):
📊 **Заголовок с цифрой**
"Только что узнал..." или "Смотрю на рынок и вижу..."
Анализ + что это значит для читателей.
⚡️ **Главный инсайт жирным**

ПРАВИЛА:
- Markdown: **жирный**, _курсив_
- Эмодзи 10-15 штук: 🏠🏗️🔑💰📈📊🌟⚡️🎯💡🔥✅❌🤔💬👇🏆💎🌍✈️📍🏖️🌆💸🤑🎉🙌😎🤝
- Районы: Dubai Marina, JBR, Business Bay, Downtown, Palm Jumeirah, Creek Harbour
- Застройщики: Emaar, Damac, Nakheel, Sobha, Aldar
- СТРОГО до 800 символов включая эмодзи
- 3-4 абзаца максимум
- БЕЗ хэштегов, БЕЗ горизонтальных линий
"""

FOOTER = """

⁉️ Хотите выгодно инвестировать или купить жильё в Дубае?

📸 [Instagram](https://www.instagram.com/juliia_mart?igsh=MzR0anMycTg4M2V2) | 📺 [YouTube](https://m.youtube.com/@top_family_dxb) | 📨 [Telegram](https://t.me/top_family_manager)"""

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
    return _call_claude(prompt, add_footer=(platform == "telegram"))


# Полный список тем — 60+ уникальных
ALL_TOPICS = [
    # Районы и локации
    "Dubai Marina в 2026 — стоит ли покупать или уже поздно?",
    "JBR vs Palm Jumeirah: где реально лучше жить и инвестировать",
    "Business Bay — недооценённый район или пузырь?",
    "Downtown Dubai: цены выросли на 40% — что дальше?",
    "Jumeirah Village Circle — лучший баланс цены и качества в 2026?",
    "Creek Harbour — ставка на будущее или риск?",
    "Dubai Hills vs Arabian Ranches: семейная недвижимость — где лучше?",
    "Damac Hills 2 — дальняя локация, но цены как в центре. Почему?",
    "MBR City: новый центр Dubai или маркетинг?",
    "Al Barsha vs Jumeirah: аренда для экспатов — где дешевле жить?",
    # Off-plan
    "Как читать договор off-plan и не попасть в ловушку",
    "Payment plan 1%/месяц — выгода или скрытые риски?",
    "Топ-5 застройщиков Dubai которым можно доверять в 2026",
    "Как проверить застройщика за 15 минут — чеклист",
    "Разница между SPA и MOU — что нужно знать до подписания",
    "Off-plan assignment: заработать на перепродаже до сдачи",
    "Когда лучше покупать off-plan — на старте или перед сдачей?",
    "Гарантия доходности от застройщика — верить или нет?",
    # Инвестиции
    "ROI 8-12% в Dubai — реально или маркетинговый трюк?",
    "Короткосрочная аренда (Airbnb) в Dubai: цифры и реальность",
    "Долгосрочная аренда vs Airbnb: что выгоднее в 2026?",
    "Как считать реальную доходность недвижимости в Dubai",
    "Топ-5 районов Dubai по доходности аренды в 2026",
    "Инвестиции в парковку в Dubai — неочевидный способ заработать",
    "Коммерческая недвижимость в Dubai: офисы, склады, ретейл",
    "Покупка недвижимости в Dubai через компанию — плюсы и минусы",
    "REITs vs прямая покупка: что лучше для пассивного инвестора?",
    # Юридическое и финансовое
    "Golden Visa через недвижимость — полный гайд 2026",
    "DLD fees, agency fee, NOC — все расходы при покупке",
    "Ипотека в Dubai для иностранцев: условия и реальность",
    "Freehold vs Leasehold — в чём разница и где покупать?",
    "Как открыть счёт в банке Dubai при покупке недвижимости",
    "Налоги при продаже недвижимости в Dubai — есть или нет?",
    "Наследование недвижимости в Dubai — что нужно знать",
    "Страхование недвижимости в Dubai — обязательно или нет?",
    # Рынок и тренды
    "Почему цены в Dubai не падают даже в кризис",
    "Экспаты бегут в Dubai: откуда едут и куда покупают",
    "Сезонность рынка Dubai — когда покупать выгоднее?",
    "Crypto и недвижимость Dubai — как платить биткоином",
    "Sustainable недвижимость в Dubai — тренд или необходимость?",
    "Влияние геополитики на рынок Dubai: что происходит?",
    "Рынок luxury в Dubai — кто покупает апартаменты за $5M+?",
    "Branded residences в Dubai: Versace, Bugatti, Armani — зачем?",
    # Практические советы
    "Как найти хорошего брокера в Dubai и не нарваться на мошенника",
    "10 вопросов которые нужно задать брокеру перед покупкой",
    "Осмотр квартиры в Dubai перед покупкой: что проверить",
    "Сдача в аренду в Dubai: самостоятельно или через управляющую компанию?",
    "Как правильно торговаться при покупке недвижимости в Dubai",
    "Переезд в Dubai: что нужно сделать до покупки жилья",
    "Типичные ошибки русских при покупке недвижимости в Dubai",
    "Вторичный рынок vs первичный: что лучше в 2026?",
    # Личные истории и кейсы
    "История клиента: купил студию за $150K — продал за $230K за 2 года",
    "Как семья из Москвы переехала в Dubai и что купила",
    "Кейс: инвестор вложил $500K в 5 студий — считаем доход",
    "Как получить Golden Visa за 30 дней — реальная история",
    "Почему я продал квартиру в Москве и купил две в Dubai",
]

def _get_unused_topic() -> str:
    """Возвращает тему которая ещё не использовалась недавно."""
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
    
    # Берём темы которых нет в последних 20 использованных
    available = [t for t in ALL_TOPICS if t not in used[-20:]]
    if not available:
        available = ALL_TOPICS
    
    topic = random.choice(available)
    
    # Сохраняем в историю
    used.append(topic)
    used = used[-30:]  # Храним только последние 30
    try:
        with open(history_file, 'w') as f:
            json.dump(used, f, ensure_ascii=False)
    except Exception:
        pass
    
    return topic


def generate_tip_post(platform: str = "telegram") -> Optional[str]:
    """Генерирует полезный совет для покупателей/инвесторов."""
    topic = _get_unused_topic()
    style = CHANNEL_STYLE if platform == "telegram" else THREADS_STYLE

    prompt = f"""
{style}

Напиши экспертный пост на тему: «{topic}»

Пост должен быть практичным, конкретным и полезным для русскоязычного покупателя или инвестора.
Используй реальные цифры, примеры, конкретные районы и застройщики.
Напиши только текст поста, без кавычек и пояснений.
"""
    return _call_claude(prompt, add_footer=(platform == "telegram"))


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
    return _call_claude(prompt, add_footer=(platform == "telegram"))


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
                # Генерируем поисковый запрос для фото на основе текста
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
    """Планирует микс типов постов на день."""
    if count <= 3:
        return ["news", "tip", "insight"][:count]
    elif count <= 5:
        return ["news", "tip", "news", "insight", "tip"][:count]
    else:
        base = ["news", "tip", "news", "insight", "tip"]
        return (base * 2)[:count]


def _generate_photo_query(text: str, post_type: str) -> str:
    """Генерирует детальный промпт для AI генерации изображения через fal.ai."""
    prompt = f"""На основе этого текста поста о недвижимости Dubai создай детальный промпт для AI генерации изображения.

Текст поста:
{text[:600]}

Создай промпт на английском (10-20 слов) который описывает идеальное фото для этого поста.
Промпт должен быть конкретным и РАЗНООБРАЗНЫМ — не всегда интерьер с закатом!

Возможные варианты:
- Аэросъёмка: "Palm Jumeirah aerial view, turquoise water, luxury villas"
- Экстерьер здания: "Dubai Marina luxury tower exterior, glass facade, blue sky"
- Улица/набережная: "Dubai Marina walk promenade, yachts, modern buildings"
- Панорама города: "Downtown Dubai skyline panorama, Burj Khalifa, night lights"
- Бассейн/терраса: "Infinity pool Dubai skyscraper rooftop, city view"
- Интерьер (редко): "Luxury Dubai penthouse living room, panoramic windows"
- Строительство: "Dubai construction site cranes, new development, modern"
- Пляж/море: "JBR beach Dubai, luxury hotels, turquoise water, clear sky"

Выбирай тип сцены который лучше всего соответствует теме поста.
Только промпт без объяснений:

Только промпт, без объяснений:"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{"role": "user", "content": prompt}]
        )
        query = response.content[0].text.strip().strip('"').strip("'")
        logger.info(f"Image prompt generated: {query}")
        return query
    except Exception as e:
        logger.warning(f"Image prompt generation failed: {e}")
        defaults = {
            "news": "Dubai skyline luxury architecture golden hour",
            "tip": "Dubai luxury apartment interior modern design",
            "insight": "Dubai aerial cityscape Palm Jumeirah drone view",
        }
        return defaults.get(post_type, "Dubai luxury real estate")


def _call_claude(prompt: str, add_footer: bool = False) -> Optional[str]:
    """Вызывает Claude API."""
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Жёсткое ограничение — caption Telegram максимум 1024 символа
        # Оставляем 150 символов для footer
        MAX_LEN = 870
        if len(text) > MAX_LEN:
            # Обрезаем по последнему абзацу
            cut = text[:MAX_LEN]
            last_para = cut.rfind("\n\n")
            if last_para > 400:
                text = cut[:last_para].strip()
            else:
                last_sent = cut.rfind(".")
                if last_sent > 400:
                    text = cut[:last_sent + 1].strip()
                else:
                    text = cut.strip()
        if add_footer:
            text = text + FOOTER
        return text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None
