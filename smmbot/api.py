import aiohttp
from config import SMM_API_KEY, SMM_API_URL, DEFAULT_MARKUP, logger

async def smm_request(action, **kwargs):
    params = {"key": SMM_API_KEY, "action": action}
    params.update(kwargs)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SMM_API_URL, data=params, timeout=30) as resp:
                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    text = await resp.text()
                    logger.error(f"API javobi JSON emas: {text[:200]}")
                    return {"error": "API noto'g'ri formatda javob qaytardi"}
    except aiohttp.ClientError as e:
        logger.error(f"API ulanish xatosi: {e}")
        return {"error": f"Ulanish xatosi: {str(e)}"}
    except Exception as e:
        logger.error(f"API so'rovida kutilmagan xato: {e}")
        return {"error": f"Kutilmagan xato: {str(e)}"}

async def fetch_all_services():
    data = await smm_request("services")
    if "error" in data:
        logger.error(f"API import xatosi: {data['error']}")
        return None, data['error']
    if not isinstance(data, list):
        logger.error(f"API noto'g'ri format: {type(data)}")
        return None, "API dan kutilgan ro'yxat (list) kelmadi"
    categories_dict = {}
    for item in data:
        cat = item.get('category', 'Boshqa')
        if cat not in categories_dict:
            categories_dict[cat] = []
        try:
            api_rate = float(item.get('rate', 0))
        except (TypeError, ValueError):
            api_rate = 0.0
        admin_price = round(api_rate + DEFAULT_MARKUP, 2)
        service_info = {
            'service_id': item.get('service'),
            'name': item.get('name'),
            'rate': api_rate,
            'admin_price': admin_price,
            'min': item.get('min', 1),
            'max': item.get('max', 10000),
            'type': item.get('type', 'Default')
        }
        categories_dict[cat].append(service_info)
    logger.info(f"✅ API dan {sum(len(v) for v in categories_dict.values())} ta xizmat import qilindi")
    return categories_dict, None

async def create_order(api_service_id, link, quantity):
    return await smm_request("add", service=api_service_id, link=link, quantity=quantity)

async def check_order_status(api_order_id):
    return await smm_request("status", order=api_order_id)

async def get_balance():
    return await smm_request("balance")

async def cancel_order(api_order_id):
    return await smm_request("cancel", order=api_order_id)

async def refill_order(api_order_id):
    return await smm_request("refill", order=api_order_id)
