import datetime
from aiogram import types, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS, logger
from database import (
    add_user, get_user, update_balance, get_all_users, get_user_by_username,
    get_all_categories, get_services_by_category, get_service,
    add_order, get_user_orders, get_user_active_orders, get_order, update_order_status,
    add_favorite_db, remove_favorite_db, get_favorites,
    save_referral, get_referral_count, get_total_referrals, get_top_referrers,
    add_payment, get_pending_payments, update_payment_status, get_payment,
    add_question, get_user_questions, get_pending_questions, answer_question,
    get_active_contest, get_card, add_category
)
from api import create_order
from keyboards import (
    main_menu,
    back_to_main,
    user_service_buttons,
    confirm_order as confirm_order_kb,
    back_button
)
from states import *

router = Router()

# ==================== /START ====================
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("_")[1])
        except:
            pass

    add_user(message.from_user.id, message.from_user.username, message.from_user.full_name, referrer_id)

    if referrer_id and referrer_id != message.from_user.id:
        save_referral(message.from_user.id, referrer_id)
        await message.bot.send_message(referrer_id, f"👥 Sizning taklifingiz bo'yicha yangi foydalanuvchi keldi! 🎉 Siz konkursda ishtirok eta olasiz!")

    # 👇 Admin tugmasi uchun user_id uzatamiz
    await message.answer("🏠 Bosh menyu", reply_markup=main_menu(message.from_user.id))

# ==================== MENU TUGMALARI ====================
@router.callback_query(F.data.startswith("menu_"))
async def menu_actions(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    action = callback.data.split("_")[1]

    if action == "services":
        await show_categories(callback)
    elif action == "favorites":
        await show_favorites(callback)
    elif action == "contest":
        await show_contest(callback)
    elif action == "status":
        await show_active_orders(callback)
    elif action == "history":
        await show_order_history(callback)
    elif action == "account":
        await show_account(callback)
    elif action == "refill":
        await start_refill(callback, state)
    elif action == "referral":
        await show_referral(callback)
    elif action == "contact":
        await start_contact(callback, state)
    elif action == "questions":
        await show_questions(callback, state)
    await callback.answer()

# ==================== 1. XIZMATLAR (USER) ====================
async def show_categories(callback: types.CallbackQuery):
    categories = get_all_categories()
    if not categories:
        await callback.message.edit_text(
            "📭 Hozircha xizmatlar mavjud emas.\n\n⚠️ Admin API dan xizmatlarni import qilishi kerak.",
            reply_markup=back_to_main()
        )
        return

    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=f"{cat['name']}", callback_data=f"user_cat_view_{cat['id']}")
    kb.button(text="🔙 Orqaga", callback_data="back_main")
    kb.adjust(2)
    await callback.message.edit_text("📂 Kategoriyani tanlang:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("user_cat_view_"))
async def show_services(callback: types.CallbackQuery):
    cat_id = int(callback.data.split("_")[3])
    services = get_services_by_category(cat_id)

    if not services:
        await callback.message.edit_text("📭 Bu kategoriyada xizmatlar yo'q.", reply_markup=back_to_main())
        return

    kb = InlineKeyboardBuilder()
    for srv in services:
        kb.button(text=f"{srv['name']} ({srv['admin_price']} so'm/1000 dona)", callback_data=f"user_srv_{srv['id']}")
    kb.button(text="🔙 Orqaga", callback_data="menu_services")
    kb.adjust(1)
    await callback.message.edit_text("📋 Xizmatni tanlang:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("user_srv_"))
async def select_service(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[2])
    await state.update_data(service_id=service_id)

    service = get_service(service_id)
    await callback.message.edit_text(
        f"📋 {service['name']}\n💰 Narxi: {service['admin_price']} so'm / 1000 dona\n📊 Min: {service['min']} | Max: {service['max']}\n\nXizmatni tanladingiz. Endi nima qilamiz?",
        reply_markup=user_service_buttons(service_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("user_order_now_"))
async def order_now(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[3])
    await state.update_data(service_id=service_id)
    await callback.message.edit_text("📎 Iltimos, havola (link) ni yuboring:")
    await state.set_state(OrderStates.get_link)
    await callback.answer()

# ============ SEVIMLILARGA QO'SHISH (TUZATILGAN) ============
@router.callback_query(F.data.startswith("user_add_fav_"))
async def add_favorite_handler(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[3])
    add_favorite_db(callback.from_user.id, service_id)   # <-- database funksiyasi
    await callback.message.edit_text("✅ Xizmat sevimlilarga qo'shildi!", reply_markup=back_to_main())
    await callback.answer()

# ==================== BUYURTMA BERISH (USER) ====================
@router.message(OrderStates.get_link)
async def get_link(message: types.Message, state: FSMContext):
    await state.update_data(link=message.text)
    await message.answer("🔢 Nechta dona kerak? (son kiriting):")
    await state.set_state(OrderStates.get_quantity)

@router.message(OrderStates.get_quantity)
async def get_quantity(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting!")
        return

    quantity = int(message.text)
    data = await state.get_data()
    service = get_service(data['service_id'])

    if quantity < service['min'] or quantity > service['max']:
        await message.answer(f"❌ Min: {service['min']}, Max: {service['max']} oralig'ida bo'lishi kerak.")
        return

    await state.update_data(quantity=quantity)
    total_price = (quantity / 1000) * service['admin_price']
    user = get_user(message.from_user.id)

    await message.answer(
        f"📝 Buyurtma ma'lumotlari:\n"
        f"Xizmat: {service['name']}\n"
        f"Link: {data['link']}\n"
        f"Soni: {quantity}\n"
        f"💰 Narxi: {total_price:.2f} so'm\n"
        f"💳 Balansingiz: {user['balance']:.2f} so'm",
        reply_markup=confirm_order_kb()
    )
    await state.set_state(OrderStates.confirm)

@router.callback_query(F.data == "user_confirm_order")
async def user_confirm_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service = get_service(data['service_id'])
    total_price = (data['quantity'] / 1000) * service['admin_price']
    user = get_user(callback.from_user.id)

    if user['balance'] < total_price:
        await callback.message.edit_text("❌ Balansingiz yetarli emas! Iltimos, balansni to'ldiring.", reply_markup=back_to_main())
        await state.clear()
        return

    api_resp = await create_order(service['api_service_id'], data['link'], data['quantity'])

    if "error" in api_resp:
        await callback.message.edit_text(f"❌ API xatosi: {api_resp['error']}", reply_markup=back_to_main())
        await state.clear()
        return

    api_order_id = api_resp.get("order")
    price = float(api_resp.get("price", total_price))

    order_id = add_order(callback.from_user.id, data['service_id'], data['link'], data['quantity'], total_price, api_order_id)
    update_balance(callback.from_user.id, -total_price)

    await callback.message.edit_text(
        f"✅ Buyurtma qabul qilindi!\n🆔 Buyurtma #: {order_id}\nAPI ID: {api_order_id}\n💰 Yechildi: {total_price:.2f} so'm",
        reply_markup=back_to_main()
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "user_cancel_order")
async def user_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.", reply_markup=back_to_main())
    await state.clear()
    await callback.answer()

# ==================== 2. SEVIMLILAR (USER) ====================
async def show_favorites(callback: types.CallbackQuery):
    favs = get_favorites(callback.from_user.id)
    if not favs:
        await callback.message.edit_text("⭐ Sevimlilar ro'yxati bo'sh.", reply_markup=back_to_main())
        return

    kb = InlineKeyboardBuilder()
    for srv in favs:
        kb.button(text=f"{srv['name']} ({srv['admin_price']} so'm/1000 dona)", callback_data=f"user_srv_{srv['id']}")
        kb.button(text="🗑️", callback_data=f"user_del_fav_{srv['id']}")
    kb.button(text="🔙 Orqaga", callback_data="back_main")
    kb.adjust(2)
    await callback.message.edit_text("⭐ Sevimli xizmatlaringiz:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("user_del_fav_"))
async def delete_favorite_handler(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[3])
    remove_favorite_db(callback.from_user.id, service_id)   # <-- database funksiyasi
    await callback.message.edit_text("✅ Sevimlilardan o'chirildi!")
    await show_favorites(callback)
    await callback.answer()

# ==================== 3. KONKURS (USER) ====================
async def show_contest(callback: types.CallbackQuery):
    contest = get_active_contest()
    if not contest:
        text = "🎁 Hozirda faol konkurs yo'q."
    else:
        ref_count = get_referral_count(callback.from_user.id)
        total_participants = get_total_referrals()
        top_users = get_top_referrers(10)

        position = None
        for i, user in enumerate(top_users, 1):
            if user['referrer_id'] == callback.from_user.id:
                position = i
                break

        text = f"🎁 {contest['title']}\n\n📝 {contest['description']}\n\n"
        text += f"📅 Boshlangan: {contest['start_date'][:10]}\n📅 Tugash: {contest['end_date'][:10]}\n\n"
        text += f"🏆 Sovg'alar:\n🥇 1-o'rin: {contest['prize_1']}\n🥈 2-o'rin: {contest['prize_2']}\n🥉 3-o'rin: {contest['prize_3']}\n\n"
        text += f"👥 Sizning taklif qilganlar: {ref_count} ta\n"
        text += f"📊 Jami qatnashchilar: {total_participants} ta\n"
        text += f"🏅 Sizning o'rningiz: {position if position else 'TOP 10 da emas'}\n\n"

        if top_users:
            text += "📊 TOP 3:\n"
            for i, user in enumerate(top_users[:3], 1):
                u = get_user(user['referrer_id'])
                username = u['username'] if u else str(user['referrer_id'])
                text += f"{i}. @{username} - {user['count']} ta taklif\n"

    await callback.message.edit_text(text, reply_markup=back_to_main())
    await callback.answer()

# ==================== 4. BUYURTMA HOLATI (USER) ====================
async def show_active_orders(callback: types.CallbackQuery):
    orders = get_user_active_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text("📊 Hozirda faol buyurtmangiz yo'q.", reply_markup=back_to_main())
        return

    text = "📊 Sizning faol buyurtmalaringiz:\n\n"
    for o in orders:
        status_emoji = {'Pending': '⏳', 'Processing': '🔄', 'Completed': '✅', 'Cancelled': '❌'}.get(o['status'], '❓')
        text += f"{status_emoji} #{o['id']} - {o['service_name']}\n   Soni: {o['quantity']} | Narx: {o['price']:.2f} so'm\n   Holat: {o['status']}\n\n"

    await callback.message.edit_text(text, reply_markup=back_to_main())
    await callback.answer()

# ==================== 5. BUYURTMA TARIXI (USER) ====================
async def show_order_history(callback: types.CallbackQuery):
    orders = get_user_orders(callback.from_user.id, 20)
    if not orders:
        await callback.message.edit_text("📜 Siz hali buyurtma bermagansiz.", reply_markup=back_to_main())
        return

    text = "📜 Oxirgi 20 ta buyurtmangiz:\n\n"
    for o in orders:
        status_emoji = {'Pending': '⏳', 'Processing': '🔄', 'Completed': '✅', 'Cancelled': '❌'}.get(o['status'], '❓')
        text += f"{status_emoji} #{o['id']} - {o['service_name']}\n   {o['quantity']} dona | {o['price']:.2f} so'm | {o['status']}\n\n"

    await callback.message.edit_text(text, reply_markup=back_to_main())
    await callback.answer()

# ==================== 6. MENING HISOBIM (USER) ====================
async def show_account(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    ref_count = get_referral_count(callback.from_user.id)
    contest = get_active_contest()

    text = f"👤 Hisobingiz\n🆔 ID: {user['user_id']}\n👤 Ism: {user['full_name']}\n💰 Balans: {user['balance']:.2f} so'm\n👥 Taklif qilganlar: {ref_count} ta\n"

    if contest:
        top_users = get_top_referrers(10)
        position = None
        for i, u in enumerate(top_users, 1):
            if u['referrer_id'] == callback.from_user.id:
                position = i
                break
        text += f"🏆 Konkursdagi o'rni: {position if position else 'TOP 10 da emas'}\n"

    text += f"📅 Qo'shilgan: {user['join_date'][:10]}"

    await callback.message.edit_text(text, reply_markup=back_to_main())
    await callback.answer()

# ==================== 7. BALANS TO'LDIRISH (USER) ====================
async def start_refill(callback: types.CallbackQuery, state: FSMContext):
    card = get_card()
    text = "💳 Balansni to'ldirish\n\n"
    if card:
        text += f"💳 Karta raqami: {card['card_number']}\n👤 Ism: {card['full_name']}\n\n"
    text += "📝 Summani kiriting (minimal 1000 so'm):"

    await callback.message.edit_text(text, reply_markup=back_to_main())
    await state.set_state(RefillStates.get_amount)
    await callback.answer()

@router.message(RefillStates.get_amount)
async def get_refill_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 1000:
            await message.answer("❌ Minimal summa 1000 so'm. Qaytadan kiriting:")
            return
    except:
        await message.answer("❌ Iltimos, son kiriting (masalan: 50000):")
        return

    await state.update_data(amount=amount)
    await message.answer("📷 To'lov chekini (rasm/screenshot) yuboring:")
    await state.set_state(RefillStates.get_check)

@router.message(RefillStates.get_check, F.photo)
async def get_check_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id

    add_payment(message.from_user.id, data['amount'], file_id)

    for admin_id in ADMIN_IDS:
        await message.bot.send_photo(
            admin_id,
            photo=file_id,
            caption=f"💳 Yangi to'lov so'rovi!\n👤 Foydalanuvchi: @{message.from_user.username}\n🆔 ID: {message.from_user.id}\n💰 Summa: {data['amount']} so'm"
        )

    await message.answer(f"✅ So'rovingiz qabul qilindi!\n💰 Summa: {data['amount']} so'm\n\nAdmin tekshirib, tasdiqlagach balansingizga qo'shiladi.", reply_markup=back_to_main())
    await state.clear()

@router.message(RefillStates.get_check)
async def invalid_check(message: types.Message):
    await message.answer("❌ Iltimos, rasm (screenshot) yuboring!")

# ==================== 8. DO'STNI TAKLIF QILISH (USER) ====================
async def show_referral(callback: types.CallbackQuery):
    bot_info = await callback.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    ref_count = get_referral_count(callback.from_user.id)
    contest = get_active_contest()

    text = "👥 Do'stlaringizni taklif qiling va konkursda ishtirok eting!\n\n✅ Har bir taklif qilgan do'stingiz botga kirganda, siz **konkursda bir ball** olasiz. Kim ko'p odam taklif qilsa, u g'olib bo'ladi!\n\n"
    text += f"🔗 Sizning taklif havolangiz:\n{link}\n\n📊 Taklif qilganlar: {ref_count} ta\n"

    if contest:
        top_users = get_top_referrers(10)
        position = None
        for i, u in enumerate(top_users, 1):
            if u['referrer_id'] == callback.from_user.id:
                position = i
                break
        text += f"🏆 Konkursdagi o'rningiz: {position if position else 'TOP 10 da emas'}\n"

    await callback.message.edit_text(text, reply_markup=back_to_main())
    await callback.answer()

# ==================== 9. ADMIN BILAN ALOQA (USER) ====================
async def start_contact(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📞 Admin bilan bog'lanish uchun xabaringizni yozing:", reply_markup=back_to_main())
    await state.set_state(ContactStates.get_message)
    await callback.answer()

@router.message(ContactStates.get_message)
async def send_contact_message(message: types.Message, state: FSMContext):
    text = f"📩 Foydalanuvchi @{message.from_user.username} (ID: {message.from_user.id}) dan xabar:\n\n{message.text}"
    for admin_id in ADMIN_IDS:
        await message.bot.send_message(admin_id, text)
    await message.answer("✅ Xabaringiz adminga yuborildi! Tez orada javob beramiz.", reply_markup=back_to_main())
    await state.clear()

# ==================== 10. SAVOLLAR (USER) ====================
async def show_questions(callback: types.CallbackQuery, state: FSMContext):
    questions = get_user_questions(callback.from_user.id)
    kb = InlineKeyboardBuilder()

    text = "❓ Savollaringiz\n\n"
    if questions:
        for q in questions:
            status = "✅ Javob berilgan" if q['status'] == 'answered' else "⏳ Javobsiz"
            text += f"📝 Savol: {q['question'][:50]}...\n📊 Holat: {status}\n"
            if q['answer']:
                text += f"📨 Javob: {q['answer']}\n"
            text += "---\n"
    else:
        text += "Siz hali savol bermagansiz.\n"

    kb.button(text="➕ Yangi savol qo'shish", callback_data="user_add_question")
    kb.button(text="🔙 Orqaga", callback_data="back_main")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data == "user_add_question")
async def ask_question(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍️ Savolingizni yozing:")
    await state.set_state(QuestionStates.ask_question)
    await callback.answer()

@router.message(QuestionStates.ask_question)
async def save_question(message: types.Message, state: FSMContext):
    add_question(message.from_user.id, message.text)
    await message.answer("✅ Savolingiz qabul qilindi!\nAdmin javob yozgach, bu yerda ko'rasiz.", reply_markup=back_to_main())
    await state.clear()

# ==================== ORQAGA QAYTISH ====================
@router.callback_query(F.data == "back_main")
async def back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    # 👇 Admin tugmasi uchun user_id uzatamiz
    await callback.message.edit_text("🏠 Bosh menyu", reply_markup=main_menu(callback.from_user.id))
    await callback.answer()

@router.callback_query(F.data == "user_back_services")
async def back_services(callback: types.CallbackQuery):
    await show_categories(callback)
    await callback.answer()

# ==================== /STATUS (USER) ====================
@router.message(Command("status"))
async def cmd_status(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Ishlatish: /status <order_id>")
        return

    try:
        order_id = int(parts[1])
    except:
        await message.answer("❌ Noto'g'ri format. Son kiriting!")
        return

    order = get_order(order_id)
    if not order or order['user_id'] != message.from_user.id:
        await message.answer("❌ Buyurtma topilmadi yoki sizga tegishli emas.")
        return

    service = get_service(order['service_id'])
    status_emoji = {'Pending': '⏳', 'Processing': '🔄', 'Completed': '✅', 'Cancelled': '❌'}.get(order['status'], '❓')

    await message.answer(
        f"📊 Buyurtma #{order_id}\nXizmat: {service['name']}\nHolat: {status_emoji} {order['status']}\nSoni: {order['quantity']}\nNarx: {order['price']:.2f} so'm\nLink: {order['link']}"
    )