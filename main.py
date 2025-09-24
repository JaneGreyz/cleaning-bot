import os
from aiogram import Bot, Dispatcher
from handlers import router
from database import init_db
from dotenv import load_dotenv
from flask import Flask
import threading

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

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    # Запускаем бота
    import asyncio
    asyncio.run(start_bot())