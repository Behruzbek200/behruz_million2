import os
import asyncio
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, logger
from database import create_tables
from handlers_user import router as user_router
from handlers_admin import router as admin_router

# ==================== FLASK ILOVASI ====================
app = Flask(__name__)

# ==================== BOT VA DISPATCHER ====================
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Routerlarni ulash
dp.include_router(user_router)
dp.include_router(admin_router)

# ==================== WEBHOOK ENDPOINT ====================
@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram dan kelgan update ni qayta ishlaydi"""
    update_data = request.get_json()
    if not update_data:
        return jsonify({"ok": False}), 400
    
    try:
        update = Update(**update_data)
        # Async funksiyani sinxron ishga tushirish
        asyncio.run(dp.process_update(update))
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Webhook xatosi: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ==================== WEBHOOK O'RNATISH ====================
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Botning webhook manzilini o'rnatadi"""
    # Render.com da RENDER_EXTERNAL_URL avtomatik beriladi
    base_url = os.getenv('RENDER_EXTERNAL_URL', 'https://your-bot.onrender.com')
    webhook_url = f"{base_url}/webhook"
    
    try:
        asyncio.run(bot.set_webhook(webhook_url))
        logger.info(f"Webhook o'rnatildi: {webhook_url}")
        return jsonify({"ok": True, "webhook_url": webhook_url})
    except Exception as e:
        logger.error(f"Webhook o'rnatish xatosi: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ==================== ROOT ENDPOINT ====================
@app.route('/')
def index():
    return "SMM Bot ishlamoqda! Webhook manzili: /webhook"

# ==================== ISHGA TUSHIRISH ====================
if __name__ == '__main__':
    # Ma'lumotlar bazasini yaratish
    create_tables()
    logger.info("Flask ilovasi ishga tushdi!")
    
    # Local testing uchun
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)