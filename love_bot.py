import random
import asyncio
import os
from datetime import datetime, timedelta
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

active_countdowns = {}
users = set()
notified_24h = False
notified_1h = False

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


def format_time(delta, mode="full"):
    total = int(delta.total_seconds())
    days = total // 86400
    hours = (total % 86400) // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60

    if mode == "hours":
        return f"*{hours}* ч. *{minutes}* мин. *{seconds}* сек."
    elif mode == "minutes":
        return f"*{minutes}* мин. *{seconds}* сек."
    else:
        return f"*{days}* дн. *{hours}* ч. *{minutes}* мин. *{seconds}* сек."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users.add(user.id)

    print(f"[START] {datetime.now(MSK)} | ID: {user.id} | @{user.username}")

    await update.message.reply_text(
        "✨ Нажми кнопку ниже ✨",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💌 Узнать время до встречи", callback_data="start_timer")]
        ])
    )


async def start_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    users.add(user.id)

    print(f"[TIMER START/RESTART] {datetime.now(MSK)} | ID: {user.id}")

    # Если есть старый таймер — корректно его останавливаем
    if user.id in active_countdowns:
        try:
            active_countdowns[user.id]["task"].cancel()
        except:
            pass

        try:
            await active_countdowns[user.id]["message"].delete()
        except:
            pass

        del active_countdowns[user.id]

    # Создаём новое сообщение
    message = await query.message.reply_text("❤️ Таймер запущен ❤️")

    # Создаём новую задачу
    task = context.application.create_task(run_timer(user.id, message))

    active_countdowns[user.id] = {
        "task": task,
        "message": message
    }


async def run_timer(user_id, message):
    global notified_24h, notified_1h

    phrase = random.choice(LOVE_PHRASES)
    last_phrase_change = datetime.now(MSK)

    try:
        while True:
            now = datetime.now(MSK)
            delta = MEETING_TIME - now

            if delta.total_seconds() <= 10:
                await cinematic_finale(message)
                break

            if (now - last_phrase_change).total_seconds() >= 5:
                phrase = random.choice(LOVE_PHRASES)
                last_phrase_change = now

            if delta <= timedelta(hours=1):
                mode = "minutes"
            elif delta <= timedelta(hours=24):
                mode = "hours"
            else:
                mode = "full"

            text = (
                "💖 До нашей встречи осталось 💖\n\n"
                f"⏳ {format_time(delta, mode)}\n\n"
                f"{phrase}"
            )

            try:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=keyboard()
                )
            except RetryAfter as e:
                print(f"[FloodWait] Ждём {e.retry_after}")
                await asyncio.sleep(e.retry_after)
            except BadRequest:
                break

            await asyncio.sleep(1)

    except asyncio.CancelledError:
        pass


async def cinematic_finale(message):
    print("[FINALE START]")

    for i in range(10, 0, -1):
        await message.edit_text(f"💓 {i}...\nЯ уже рядом...")
        await asyncio.sleep(1)

    frames = ["💖", "💖💖", "💖💖💖", "💞💞💞", "💘💘💘"]

    for frame in frames:
        await message.edit_text(frame)
        await asyncio.sleep(0.5)

    await message.edit_text(
        "🎆✨ МЫ ВСТРЕТИЛИСЬ!!! ✨🎆\n\n"
        "Это больше не ожидание.\n"
        "Это — наша реальность ❤️"
    )

    print("[FINALE DONE]")


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_timer(update, context)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(start_timer, pattern="start_timer"))
app.add_handler(CallbackQueryHandler(restart, pattern="restart"))

print("Бот запущен...")
app.run_polling(drop_pending_updates=True)