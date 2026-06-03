"""
main.py — Content Bot для Dubai Real Estate канала
Функции:
- Генерация постов по расписанию
- Модерация через Telegram (одобрить/отклонить/редактировать)
- Публикация в Telegram канал + Threads
"""

import asyncio
import logging
import os
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import storage
import parser as news_parser
import generator
from threads_publisher import publish_to_threads

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── ENV ───────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])          # Твой Telegram user_id
CHANNEL_ID = os.environ["CHANNEL_ID"]           # @username или -100xxxxxxxxx

# Состояние для редактирования
EDIT_TEXT = 1


# ── Клавиатура модерации ──────────────────────────────────────────────────────
def moderation_kb(post_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"approve:{post_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{post_id}"),
        ],
        [
            InlineKeyboardButton("✏️ Редактировать TG", callback_data=f"edit_tg:{post_id}"),
            InlineKeyboardButton("✏️ Редактировать TH", callback_data=f"edit_th:{post_id}"),
        ],
    ])


# ── Отправка поста на модерацию ───────────────────────────────────────────────
async def send_for_moderation(bot: Bot, post: dict):
    type_emoji = {"news": "📰", "tip": "💡", "insight": "📊"}.get(post["type"], "📝")
    source = f"\n🔗 {post['source_url']}" if post.get("source_url") else ""

    caption = (
        f"{type_emoji} *Новый пост* | ID: `{post['id']}`\n"
        f"{'─' * 30}\n\n"
        f"*Telegram:*\n{post['telegram_text']}\n\n"
        f"{'─' * 30}\n"
        f"*Threads:*\n{post['threads_text']}"
        f"{source}"
    )

    image_url = post.get("image_url")
    if image_url:
        try:
            msg = await bot.send_photo(
                chat_id=ADMIN_ID,
                photo=image_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=moderation_kb(post["id"]),
            )
        except Exception as e:
            logger.warning(f"Failed to send photo, sending text only: {e}")
            msg = await bot.send_message(
                chat_id=ADMIN_ID,
                text=caption,
                parse_mode="Markdown",
                reply_markup=moderation_kb(post["id"]),
            )
    else:
        msg = await bot.send_message(
            chat_id=ADMIN_ID,
            text=caption,
            parse_mode="Markdown",
            reply_markup=moderation_kb(post["id"]),
        )
    storage.update_post_status(post["id"], "pending", message_id=msg.message_id)

# ── Генерация и постановка в очередь ─────────────────────────────────────────
async def generate_and_queue(bot: Bot):
    logger.info("Starting content generation cycle...")
    try:
        articles = news_parser.get_all_news()
        posts = generator.generate_batch(articles, count=5)

        if not posts:
            logger.warning("No posts generated")
            await bot.send_message(ADMIN_ID, "⚠️ Не удалось сгенерировать посты. Попробуй /generate вручную.")
            return

        ids = storage.add_to_queue(posts)
        logger.info(f"Generated {len(ids)} posts")

        # Отправляем на модерацию по одному с задержкой
        for post in storage.get_pending():
            await send_for_moderation(bot, post)
            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Generation cycle error: {e}")
        await bot.send_message(ADMIN_ID, f"❌ Ошибка генерации: {e}")


# ── Обработчики кнопок ────────────────────────────────────────────────────────
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    action, post_id = query.data.split(":", 1)
    post = storage.get_post_by_id(post_id)

    if not post:
        await query.edit_message_text("❌ Пост не найден")
        return

    if action == "approve":
        await _publish_post(query, post)

    elif action == "reject":
        storage.update_post_status(post_id, "rejected")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(
            query.message.text + "\n\n❌ *Отклонён*",
            parse_mode="Markdown",
        )

    elif action in ("edit_tg", "edit_th"):
        platform = "telegram" if action == "edit_tg" else "threads"
        ctx.user_data["editing_post_id"] = post_id
        ctx.user_data["editing_platform"] = platform
        await query.message.reply_text(
            f"✏️ Введи новый текст для *{'Telegram' if platform == 'telegram' else 'Threads'}*:",
            parse_mode="Markdown",
        )
        return EDIT_TEXT


async def _publish_post(query, post: dict):
    """Публикует одобренный пост."""
    post_id = post["id"]
    results = []
    image_url = post.get("image_url")

    # Публикация в Telegram канал
    try:
        bot = query.get_bot()
        if image_url:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=image_url,
                caption=post["telegram_text"],
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=post["telegram_text"],
            )
        results.append("✅ Telegram")
    except Exception as e:
        results.append(f"❌ Telegram: {e}")
        logger.error(f"Telegram publish error: {e}")

    # Публикация в Threads (текст, картинки через API отдельно)
    if publish_to_threads(post["threads_text"]):
        results.append("✅ Threads")
    else:
        results.append("⚠️ Threads: не настроен или ошибка")

    storage.mark_published(post_id)

    await query.edit_message_reply_markup(reply_markup=None)
        try:
        await query.edit_message_caption(
            caption=(query.message.caption or "") + f"\n\n{'  |  '.join(results)}",
            parse_mode="Markdown",
        )
    except Exception:
        await query.edit_message_text(
            text=(query.message.text or "") + f"\n\n{'  |  '.join(results)}",
            parse_mode="Markdown",
        )

async def edit_text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Принимает новый текст поста."""
    post_id = ctx.user_data.get("editing_post_id")
    platform = ctx.user_data.get("editing_platform")

    if not post_id or not platform:
        return ConversationHandler.END

    new_text = update.message.text
    storage.update_post_text(post_id, platform, new_text)

    ctx.user_data.clear()
    await update.message.reply_text("✅ Текст обновлён. Нажми одобрить на исходном сообщении.")
    return ConversationHandler.END


# ── Команды ───────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "🤖 *Content Bot — Dubai Real Estate*\n\n"
        "/generate — сгенерировать посты прямо сейчас\n"
        "/pending — показать посты ожидающие одобрения\n"
        "/stats — статистика публикаций\n"
        "/status — статус бота\n",
        parse_mode="Markdown",
    )


async def cmd_generate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("⏳ Генерирую посты, займёт ~30 секунд...")
    await generate_and_queue(ctx.bot)


async def cmd_pending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    pending = storage.get_pending()
    if not pending:
        await update.message.reply_text("✅ Нет постов на одобрении")
        return
    for post in pending:
        await send_for_moderation(ctx.bot, post)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    s = storage.stats()
    await update.message.reply_text(
        f"📊 *Статистика*\n\n"
        f"⏳ Ожидают одобрения: {s['pending']}\n"
        f"✅ Одобрено (в очереди): {s['approved']}\n"
        f"📤 Опубликовано сегодня: {s['published_today']}\n"
        f"📚 Всего опубликовано: {s['total_published']}",
        parse_mode="Markdown",
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        f"🟢 Бот работает\n"
        f"🕐 Время сервера: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"📅 Генерация постов: каждый день в 08:00, 13:00, 19:00 UTC"
    )


# ── Запуск ────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Хендлеры команд
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("generate", cmd_generate))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("status", cmd_status))

    # Кнопки модерации
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Редактирование текста
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID),
        edit_text_handler,
    ))

    # Планировщик — генерация 3 раза в день
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        generate_and_queue,
        "cron",
        hour="8,13,19",   # UTC (Dubai = UTC+4, значит 12:00, 17:00, 23:00)
        minute=0,
        args=[app.bot],
    )
    scheduler.start()

    logger.info("Content Bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
