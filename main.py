import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from handlers import router

logging.basicConfig(level=logging.INFO)


async def main():
    print(f"🔍 DIAGNOSTIKA: BOT_TOKEN uzunligi={len(BOT_TOKEN)}, repr={repr(BOT_TOKEN)}", flush=True)
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN sozlanmagan! Railway -> Variables bo'limiga BOT_TOKEN qo'shing.", flush=True)
        return
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
