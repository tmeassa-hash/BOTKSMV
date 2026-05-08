import os
import sqlite3
import random
import logging
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject

# 1. LOGGING (Xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# 2. WEB SERVER (Render "Application exited early" xatosi bermasligi uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/health')
def health():
    return "OK", 200

def run_web_server():
    # Render avtomatik beradigan PORT yoki 8080 ni ishlatadi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 3. BOT SOZLAMALARI
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Bot(token=TOKEN)
dp = Dispatcher()
DB_PATH = "database.db"

# 4. MA'LUMOTLAR BAZASI FUNKSIYALARI
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                invites INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def add_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
        conn.commit()

def add_invite(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET invites = invites + 1 WHERE user_id=?", (user_id,))
        conn.commit()

# 5. BOT BUYRUQLARI
@dp.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    add_user(user_id)

    # Referral linkni tekshirish
    if command.args:
        try:
            ref_id = int(command.args)
            if ref_id != user_id:
                # Taklif qiluvchini bazada borligini tekshirish
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT user_id FROM users WHERE user_id=?", (ref_id,))
                    if cur.fetchone():
                        add_invite(ref_id)
        except:
            pass

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    await message.answer(
        f"<b>🎉 Konkurs botiga xush kelibsiz!</b>\n\n"
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
    
    await message.answer(f"👥 Siz taklif qilgan odamlar: <b>{invites}</b> ta", parse_mode="HTML")

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
        text += f"{i}. ID: <code>{str(row[0])[:5]}***</code> — <b>{row[1]}</b> ta\n"

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
        await message.answer("G'olibni aniqlash uchun ishtirokchilar yetarli emas.")
        return winner_id = random.choice(users)[0]
    await message.answer(f"🎊 Tasodifiy g‘olib aniqlandi!\n\n🏆 ID: <code>{winner_id}</code>", parse_mode="HTML")

# 6. ASOSIY ISHGA TUSHIRISH
async def main():
    init_db()
    
    # Web serverni alohida oqimda (thread) ishga tushiramiz
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    print("Bot va Web Server ishga tushdi...")
    await dp.start_polling(bot)

if name == "main":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi")
