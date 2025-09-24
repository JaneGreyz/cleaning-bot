import os
from aiogram import Bot, Dispatcher
from handlers import router
from database import init_db
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise ValueError("BOT_TOKEN not found in .env file")

bot = Bot(token=bot_token)
dp = Dispatcher()
dp.include_router(router)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
async def webhook():
    if request.method == 'POST':
        await dp.feed_webhook_update(bot, request.get_json())
    return "Webhook is active!"

if __name__ == "__main__":
    init_db()
    print("Бот инициализирован с вебхуком...")
    port = int(os.environ.get('PORT', 10000))
    webhook_url = f"https://cleaning-bot-zena.onrender.com/"  # Замени на твой URL
    asyncio.run(bot.set_webhook(url=webhook_url))  # pyright: ignore[reportUndefinedVariable]
    app.run(host='0.0.0.0', port=port)