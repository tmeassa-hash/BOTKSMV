import os
import sqlite3
import random
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject

# Loglarni sozlash (Xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# Muhit o'zgaruvchilari (Serverdan olinadi)
TOKEN = os.getenv("8413733198:AAEq412ToouNZv-nbso5q_2NbGJy0gXfUQc")
ADMIN_ID = int(os.getenv("8768834109", 0))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Ma'lumotlar bazasi bilan ishlash
DB_PATH = "database.db"

def init_db():
    """Baza yaratish"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            invites INTEGER DEFAULT 0
        )
        """)
        conn.commit()

def add_user(user_id):
    """Yangi foydalanuvchi qo'shish"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
        conn.commit()

def add_invite(user_id):
    """Takliflar sonini oshirish"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET invites = invites + 1 WHERE user_id=?", (user_id,))
        conn.commit()

@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    add_user(user_id)

    # Referral link orqali kirganini tekshirish
    if command.args:
        try:
            ref_id = int(command.args)
            # O'ziga o'zi referral bo'lmasligi kerak
            if ref_id != user_id:
                # Taklif qiluvchi bazada borligini tekshiramiz
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT user_id FROM users WHERE user_id=?", (ref_id,))
                    if cur.fetchone():
                        add_invite(ref_id)
        except ValueError:
            pass

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"

    await message.answer(
        f"🎉 <b>Konkurs botiga xush kelibsiz!</b>\n\n"
        f"👥 Odam taklif qiling va g‘olib bo‘ling!\n\n"
        f"🔗 Sizning havolangiz:\n<code>{link}</code>\n\n"
        f"📌 Buyruqlar:\n/my - Natijangiz\n/top - Reyting",
        parse_mode="HTML"
    )

@dp.message(Command("my"))
async def my_stats(message: types.Message):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT invites FROM users WHERE user_id=?", (message.from_user.id,))
        row = cur.fetchone()
        invites = row[0] if row else 0
    
    await message.answer(f"👥 Siz taklif qilgan odamlar soni: <b>{invites}</b> ta", parse_mode="HTML")

@dp.message(Command("top"))
async def top_users(message: types.Message):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, invites FROM users WHERE invites > 0 ORDER BY invites DESC LIMIT 10")
        rows = cur.fetchall()

    if not rows:
        await message.answer("Hozircha hech kim odam taklif qilmagan.")
        return

    text = "🏆 <b>TOP 10 Taklifchilar:</b>\n\n"
    for i, row in enumerate(rows, start=1):
        text += f"{i}. ID: <code>{row[0]}</code> — <b>{row[1]}</b> ta\n"

    await message.answer(text, parse_mode="HTML")

@dp.message(Command("winner"))
async def winner_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE invites > 0")
        users = cur.fetchall()

    if not users:
        await message.answer("G'olibni aniqlash uchun kamida 1 ta taklif bo'lishi kerak.")
        return

    winner_id = random.choice(users)[0]
    await message.answer(f"🎊 Tasodifiy g‘olib aniqlandi!\n\n🏆 ID: <code>{winner_id}</code>", parse_mode="HTML")

async def main():
    init_db()
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)
    if name == "main":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
