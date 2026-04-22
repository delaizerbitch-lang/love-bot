import random
import asyncio
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from telegram.error import RetryAfter, BadRequest

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

MSK = ZoneInfo("Europe/Moscow")
MEETING_TIME = datetime(2026, 5, 1, 23, 0, 0, tzinfo=MSK)

active_timers = {}

LOVE_PHRASES = [
    "Каждую секунду жду тебя ❤️",
    "Скоро обниму тебя ❤️",
    "Я считаю минуты до нашей встречи ❤️",
    "Моё сердце ускоряется ❤️",
    "Я уже мысленно рядом ❤️",
    "Секунда ближе к твоей улыбке ❤️",
    "Скоро скажу тебе это лично ❤️",
    "Я скучаю всё сильнее ❤️",
    "Ты — моё самое главное ожидание ❤️",
    "Скоро почувствую твои объятия ❤️",
    "Я представляю этот момент каждый день ❤️",
    "Время идёт, а чувства только сильнее ❤️",
    "Каждый тик часов — ближе к тебе ❤️",
    "Я готовлю самое тёплое объятие ❤️",
    "Секунды идут слишком медленно ❤️",
    "Ты — причина моей улыбки ❤️",
    "Я жду тебя больше всего на свете ❤️",
    "Этот день станет особенным ❤️",
    "Скоро будем вместе ❤️",
    "Это ожидание стоит всего ❤️"
]


def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Перезапустить таймер", callback_data="restart")]
    ])


def format_time(delta):
    total = int(delta.total_seconds())
    days = total // 86400
    hours = (total % 86400) // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"*{days}* дн. *{hours}* ч. *{minutes}* мин. *{seconds}* сек."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # если таймер уже есть — удаляем
    if user_id in active_timers:
        try:
            active_timers[user_id]["task"].cancel()
        except:
            pass

        try:
            await active_timers[user_id]["message"].delete()
        except:
            pass

        del active_timers[user_id]

    message = await update.message.reply_text("❤️ Таймер запускается... ❤️")

    task = context.application.create_task(run_timer(user_id, message))

    active_timers[user_id] = {
        "task": task,
        "message": message
    }


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # корректно останавливаем старый таймер
    if user_id in active_timers:
        try:
            active_timers[user_id]["task"].cancel()
        except:
            pass

        try:
            await active_timers[user_id]["message"].delete()
        except:
            pass

        del active_timers[user_id]

    message = await query.message.chat.send_message("❤️ Таймер перезапущен ❤️")

    task = context.application.create_task(run_timer(user_id, message))

    active_timers[user_id] = {
        "task": task,
        "message": message
    }


async def run_timer(user_id, message):
    phrase = random.choice(LOVE_PHRASES)
    last_phrase_change = datetime.now(MSK)

    try:
        while True:
            now = datetime.now(MSK)
            delta = MEETING_TIME - now

            if delta.total_seconds() <= 0:
                await message.edit_text(
                    "🎆✨ МЫ ВСТРЕТИЛИСЬ!!! ✨🎆\n\n"
                    "Теперь это реальность ❤️"
                )
                break

            # меняем фразу каждые 5 секунд
            if (now - last_phrase_change).total_seconds() >= 5:
                phrase = random.choice(LOVE_PHRASES)
                last_phrase_change = now

            text = (
                "💖 До нашей встречи осталось 💖\n\n"
                f"⏳ {format_time(delta)}\n\n"
                f"{phrase}"
            )

            try:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=keyboard()
                )
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except BadRequest:
                # если сообщение исчезло — создаём новое
                message = await message.chat.send_message(text, parse_mode="Markdown", reply_markup=keyboard())

            await asyncio.sleep(1)

    except asyncio.CancelledError:
        pass


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(restart, pattern="restart"))

print("Бот запущен...")
app.run_polling(drop_pending_updates=True)