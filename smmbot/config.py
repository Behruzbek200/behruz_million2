import os
import logging from dotenv 
import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")

SMM_API_KEY = os.getenv("SMM_API_KEY")
if not SMM_API_KEY:
    raise ValueError("SMM_API_KEY topilmadi")

SMM_API_URL = os.getenv("SMM_API_URL", "https://smmya.com/api/v2")

ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    for item in admin_ids_str.split(','):
        if item.strip().isdigit():
            ADMIN_IDS.append(int(item.strip()))

try:
    DEFAULT_MARKUP = float(os.getenv("DEFAULT_MARKUP", 0.50))
except ValueError:
    DEFAULT_MARKUP = 0.50

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
