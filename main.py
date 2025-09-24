import asyncio
import os
from aiogram import Bot, Dispatcher
from handlers import router
from database import init_db
from dotenv import load_dotenv
from flask import Flask  # pyright: ignore[reportMissingImports]

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise ValueError("BOT_TOKEN not found in .env file")

bot = Bot(token=bot_token)
dp = Dispatcher()
dp.include_router(router)

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return "Bot is running!"

async def start_bot():
    init_db()
    print("Бот начинает опрос...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    asyncio.run(start_bot())
    app.run(host='0.0.0.0', port=port)