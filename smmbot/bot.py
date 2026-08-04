import asyncio from aiogram 
import Bot, Dispatcher from aiogram.fsm.storage.memory 
import MemoryStorage from config
import BOT_TOKEN, logger from database
import create_tables from handlers_user
import router as user_router from handlers_admin 
import router as admin_router

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Routerlarni ulash (user va admin)
dp.include_router(user_router)
dp.include_router(admin_router)

async def main():
    # Ma'lumotlar bazasidagi jadvallarni yaratish (agar mavjud bo'lmasa)
    create_tables()
    
    logger.info("Bot ishga tushdi!")
    print("✅ Bot ishga tushdi...")
    
    # Botni pollik qilish (yangiliklarni qabul qilish)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
