import random
import asyncio
import os
from datetime import datetime
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

# ✅ Получаем токен из Railway
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден! Проверь переменные Railway.")

# ✅ Дата встречи (измени на свою)
MEETING_TIME = datetime(2026, 5, 2, 18, 0, 0)

LOVE_PHRASES = [
    "Каждую секунду жду этого момента ❤️",
    "Не могу дождаться встречи с тобой ❤️",
    "Секунды тянутся, потому что я скучаю ❤️",
    "Ты даже не представляешь, как я жду тебя ❤️",
    "С каждым днём я радуюсь всё сильнее ❤️",
    "Моё сердце считает секунды до встречи ❤️",
    "Скоро обниму тебя крепко-крепко ❤️",
    "Время идёт, а чувства только сильнее ❤️",
    "Я уже мысленно рядом с тобой ❤️",
    "Каждая секунда приближает нас ❤️",
    "Жду тебя больше всего на свете ❤️",
    "Скоро увижу твою улыбку ❤️",
    "Даже часы знают, как сильно я жду ❤️",
    "Ты — самое важное ожидание в моей жизни ❤️",
    "Скоро скажу тебе это лично ❤️",
    "Я уже считаю мгновения ❤️",
    "Моё счастье приближается ❤️",
    "Скоро буду рядом и не отпущу ❤️",
    "Ты — мой самый долгожданный момент ❤️",
    "Всё вокруг напоминает о тебе ❤️"
]

# ✅ Храним активные таймеры
active_countdowns = {}

def format_time_delta(delta):
    total_seconds = int(delta.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"*{days}* дн. *{hours}* ч. *{minutes}* мин. *{seconds}* сек."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Узнать время до встречи 💌", callback_data="countdown")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✨ *Нажми кнопку ниже, чтобы узнать…* ✨",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if user_id in active_countdowns:
        await query.answer("Отсчёт уже запущен ❤️", show_alert=True)
        return

    active_countdowns[user_id] = True

    message = await query.message.edit_text(
        "💞 *Считаем секунды до встречи...* 💞",
        parse_mode="Markdown"
    )

    # ✅ запускаем фоновый таймер
    context.application.create_task(
        run_countdown_loop(user_id, message)
    )

async def run_countdown_loop(user_id, message):
    phrase = random.choice(LOVE_PHRASES)
    last_phrase_change = datetime.now()

    try:
        while True:
            now = datetime.now()

            # меняем фразу каждые 5 секунд
            if (now - last_phrase_change).total_seconds() >= 5:
                phrase = random.choice(LOVE_PHRASES)
                last_phrase_change = now

            if MEETING_TIME > now:
                delta = MEETING_TIME - now
                time_text = format_time_delta(delta)

                text = (
                    "💖 *До нашей встречи осталось:* 💖\n\n"
                    f"⏳ {time_text}\n\n"
                    f"_{phrase}_"
                )
            else:
                text = "❤️ *Мы уже вместе!* ❤️"

            await message.edit_text(text, parse_mode="Markdown")
            await asyncio.sleep(1)

    except Exception as e:
        print("Ошибка в таймере:", e)

    finally:
        active_countdowns.pop(user_id, None)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(countdown, pattern="countdown"))

print("Бот запущен...")
app.run_polling(drop_pending_updates=True)