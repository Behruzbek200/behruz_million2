import os
import traceback
from quart import Quart, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, logger
from database import create_tables
from handlers_user import router as user_router
from handlers_admin import router as admin_router

app = Quart(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Routerlarni ulash (BU MUHIM!)
dp.include_router(user_router)
dp.include_router(admin_router)

@app.route('/webhook', methods=['POST'])
async def webhook():
    data = await request.get_json()
    if not data:
        return jsonify({"ok": False}), 400

    try:
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        logger.info(f"Update {update.update_id} processed")
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Webhook xatosi: {e}\n{traceback.format_exc()}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    base_url = os.getenv('RENDER_EXTERNAL_URL', 'https://your-bot.onrender.com')
    webhook_url = f"{base_url}/webhook"
    try:
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook o'rnatildi: {webhook_url}")
        return jsonify({"ok": True, "webhook_url": webhook_url})
    except Exception as e:
        logger.error(f"Webhook o'rnatish xatosi: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/')
async def index():
    return "SMM Bot ishlamoqda! Webhook manzili: /webhook"

if __name__ == '__main__':
    create_tables()
    logger.info("Quart ilovasi ishga tushdi!")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
