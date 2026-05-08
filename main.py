import os
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# DATABASE
conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    invites INTEGER DEFAULT 0
)
""")
conn.commit()


def add_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()


def add_invite(user_id):
    cur.execute("UPDATE users SET invites = invites + 1 WHERE user_id=?", (user_id,))
    conn.commit()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)

    args = message.get_args()

    if args:
        try:
            ref_id = int(args)
            if ref_id != user_id:
                add_user(ref_id)
                add_invite(ref_id)
        except:
            pass

    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={user_id}"

    await message.answer(
f"""🎉 Konkurs botga xush kelibsiz!

👥 Odam taklif qiling va g‘olib bo‘ling!

🔗 Sizning havolangiz:
{link}

📌 Buyruqlar:
/my - Natija
/top - Reyting
"""
)


@dp.message_handler(commands=['my'])
async def my_stats(message: types.Message):
    cur.execute("SELECT invites FROM users WHERE user_id=?", (message.from_user.id,))
    row = cur.fetchone()

    invites = row[0] if row else 0

    await message.answer(f"👥 Siz taklif qilgan odamlar: {invites}")


@dp.message_handler(commands=['top'])
async def top_users(message: types.Message):
    cur.execute("SELECT user_id, invites FROM users ORDER BY invites DESC LIMIT 10")
    rows = cur.fetchall()

    text = "🏆 TOP 10:\n\n"

    for i, row in enumerate(rows, start=1):
        text += f"{i}. {row[0]} - {row[1]} ta\n"

    await message.answer(text)


@dp.message_handler(commands=['winner'])
async def winner(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT user_id FROM users WHERE invites > 0")
    users = cur.fetchall()

    if not users:
        await message.answer("Hech kim qatnashmagan.")
        return

    win = random.choice(users)[0]

    await message.answer(f"🏆 G‘olib ID: {win}")


if name == "main":
    executor.start_polling(dp, skip_updates=True)
