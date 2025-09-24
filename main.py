import asyncio
from aiogram import Bot, Dispatcher
from handlers import router
from database import init_db
from dotenv import load_dotenv
import os

async def main():
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN not found in .env file")
    
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    
    init_db()
    print("Бот начинает опрос...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())