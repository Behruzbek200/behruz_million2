import datetime
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS, logger
from database import *
from api import *
from keyboards import (
    admin_menu,
    admin_back,
    categories_list,
    services_list,
    confirm_delete,
    edit_service_buttons,
    payment_actions,
    question_actions,
    contest_admin_actions,
    user_profile_actions,
    users_list,
    card_actions,
    broadcast_confirm,
    back_to_main
)
from states import *

router = Router()

# ==================== ADMIN FILTER ====================
async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ==================== /ADMIN ====================
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    await message.answer("🔧 Admin paneli", reply_markup=admin_menu())

# ==================== ADMIN BACK HANDLER ====================
@router.callback_query(F.data == "admin_back")
async def admin_back_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🔧 Admin paneli", reply_markup=admin_menu())
    await callback.answer()

# ==================== 1. STATISTIKA ====================
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    users = get_all_users()
    orders = get_all_orders(100)
    pending_payments = get_pending_payments()
    pending_questions = get_pending_questions()
    contest = get_active_contest()

    total_users = len(users)
    today_orders = [o for o in orders if o['created_at'][:10] == datetime.datetime.now().date().isoformat()]
    total_revenue = sum(o['price'] for o in orders if o['status'] == 'Completed')

    text = f"📊 Statistika\n\n"
    text += f"👥 Jami foydalanuvchilar: {total_users}\n"
    text += f"📦 Bugungi buyurtmalar: {len(today_orders)}\n"
    text += f"💰 Jami daromad: {total_revenue:.2f} so'm\n"
    text += f"💳 Kutilayotgan to'lovlar: {len(pending_payments)} ta\n"
    text += f"❓ Javobsiz savollar: {len(pending_questions)} ta\n"
    if contest:
        text += f"🎁 Faol konkurs: {contest['title']} (tugashiga {contest['end_date'][:10]})"
    else:
        text += "🎁 Faol konkurs yo'q"

    await callback.message.edit_text(text, reply_markup=admin_back())
    await callback.answer()

# ==================== 2. BARCHA BUYURTMALAR ====================
@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    orders = get_all_orders(20)
    if not orders:
        await callback.message.edit_text("📦 Hozircha buyurtmalar yo'q.", reply_markup=admin_back())
        return

    text = "📦 Oxirgi 20 ta buyurtma:\n\n"
    kb = InlineKeyboardBuilder()
    for o in orders:
        status_emoji = {'Pending': '⏳', 'Processing': '🔄', 'Completed': '✅', 'Cancelled': '❌'}.get(o['status'], '❓')
        text += f"{status_emoji} #{o['id']} - {o['service_name']}\n"
        text += f"   👤 @{o['username'] or o['user_id']} | {o['quantity']} dona | {o['price']:.2f} so'm | {o['status']}\n\n"
        kb.button(text=f"🔄 #{o['id']}", callback_data=f"admin_order_detail_{o['id']}")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(3)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_order_detail_"))
async def admin_order_detail(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[3])
    order = get_order(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    user = get_user(order['user_id'])
    service = get_service(order['service_id'])

    text = f"📦 Buyurtma #{order_id}\n"
    text += f"👤 Foydalanuvchi: @{user['username'] or user['user_id']}\n"
    text += f"📋 Xizmat: {service['name']}\n"
    text += f"🔗 Link: {order['link']}\n"
    text += f"🔢 Soni: {order['quantity']}\n"
    text += f"💰 Narx: {order['price']:.2f} so'm\n"
    text += f"📊 Holat: {order['status']}\n"
    text += f"📅 Sana: {order['created_at'][:10]}\n"
    if order['api_order_id']:
        text += f"🆔 API ID: {order['api_order_id']}\n"

    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Bajarildi", callback_data=f"admin_order_status_{order_id}_Completed")
    kb.button(text="⏳ Jarayonda", callback_data=f"admin_order_status_{order_id}_Processing")
    kb.button(text="❌ Bekor qilish", callback_data=f"admin_order_status_{order_id}_Cancelled")
    kb.button(text="🔙 Orqaga", callback_data="admin_orders")
    kb.adjust(3)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_order_status_"))
async def order_status_change(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    order_id = int(parts[3])
    status = parts[4]
    update_order_status(order_id, status)
    await callback.answer(f"✅ Status o'zgartirildi: {status}")
    await admin_order_detail(callback)

# ==================== 3. KATEGORIYA VA XIZMATLAR ====================
@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    categories = get_all_categories()
    await callback.message.edit_text("📂 Kategoriya va Xizmatlar", reply_markup=categories_list(categories))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_cat_view_"))
async def admin_cat_view(callback: types.CallbackQuery):
    cat_id = int(callback.data.split("_")[3])
    services = get_services_by_category(cat_id)
    await callback.message.edit_text(
        f"📋 Xizmatlar (ID: {cat_id})",
        reply_markup=services_list(services, cat_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_cat_del_"))
async def admin_cat_delete(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[3])
    await state.update_data(cat_id=cat_id)
    await callback.message.edit_text("❓ Rostan ham kategoriya va undagi barcha xizmatlarni o'chirmoqchimisiz?", reply_markup=confirm_delete())
    await callback.answer()

@router.callback_query(F.data == "admin_confirm_delete_yes")
async def admin_confirm_delete_yes(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if 'cat_id' in data:
        delete_category(data['cat_id'])
        await callback.message.edit_text("✅ Kategoriya o'chirildi!", reply_markup=admin_back())
    elif 'service_id' in data:
        delete_service(data['service_id'])
        await callback.message.edit_text("✅ Xizmat o'chirildi!", reply_markup=admin_back())
    else:
        await callback.message.edit_text("❌ Xatolik yuz berdi", reply_markup=admin_back())
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "admin_confirm_delete_no")
async def admin_confirm_delete_no(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await admin_categories(callback)
    await callback.answer()

@router.callback_query(F.data == "admin_add_category")
async def admin_add_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("➕ Yangi kategoriya nomini kiriting:")
    await state.set_state(AddCategoryStates.get_name)
    await callback.answer()

@router.message(AddCategoryStates.get_name)
async def add_category_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ Nom bo'sh bo'lishi mumkin emas!")
        return
    cat_id = add_category(name)
    await message.answer(f"✅ Kategoriya yaratildi! ID: {cat_id}", reply_markup=admin_back())
    await state.clear()

# ==================== XIZMAT QO'SHISH (ADMIN) ====================
@router.callback_query(F.data.startswith("admin_add_service_"))
async def admin_add_service(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("Xatolik: noto'g'ri format", show_alert=True)
        return
    cat_id = int(parts[3])
    await state.update_data(category_id=cat_id)
    await callback.message.edit_text("🔢 Xizmat NOMI ni kiriting (mijoz ko'radi):")
    await state.set_state(AddServiceStates.get_name)
    await callback.answer()

@router.message(AddServiceStates.get_name)
async def add_service_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("🔢 API Service ID ni kiriting (smmya.com dagi ID, masalan 517):")
    await state.set_state(AddServiceStates.get_api_id)

@router.message(AddServiceStates.get_api_id)
async def add_service_api_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting!")
        return
    await state.update_data(api_id=int(message.text))
    await message.answer("💰 Narxni kiriting (1000 dona uchun so'mda, masalan 1192897.5):")
    await state.set_state(AddServiceStates.get_price)

@router.message(AddServiceStates.get_price)
async def add_service_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("❌ Iltimos, son kiriting (masalan 1192897.5)!")
        return
    if price < 0:
        await message.answer("❌ Narx manfiy bo'lishi mumkin emas!")
        return
    await state.update_data(price=price)
    await message.answer("🔢 Minimal miqdorni kiriting (masalan 1):")
    await state.set_state(AddServiceStates.get_min)

@router.message(AddServiceStates.get_min)
async def add_service_min(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, son kiriting!")
        return
    await state.update_data(min_q=int(message.text))
    await message.answer("🔢 Maksimal miqdorni kiriting (masalan 30000):")
    await state.set_state(AddServiceStates.get_max)

@router.message(AddServiceStates.get_max)
async def add_service_max(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, son kiriting!")
        return
    data = await state.get_data()
    max_q = int(message.text)
    if max_q < data['min_q']:
        await message.answer("❌ Maksimal miqdor minimaldan kichik bo'lishi mumkin emas!")
        return
    add_service(data['category_id'], data['name'], data['api_id'], data['price'], data['min_q'], max_q)
    await message.answer(
        f"✅ Xizmat qo'shildi!\n"
        f"📌 Nomi: {data['name']}\n"
        f"🆔 API ID: {data['api_id']}\n"
        f"💰 Narx (1000 dona uchun): {data['price']} so'm\n"
        f"📊 Min: {data['min_q']} | Max: {max_q}",
        reply_markup=admin_back()
    )
    await state.clear()

# ==================== XIZMATNI TAHRIRLASH (ADMIN) ====================
@router.callback_query(F.data.startswith("admin_srv_edit_"))
async def admin_srv_edit(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[3])
    await callback.message.edit_text("✏️ Nima o'zgartirmoqchisiz?", reply_markup=edit_service_buttons(service_id))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_srv_del_"))
async def admin_srv_del(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[3])
    await state.update_data(service_id=service_id)
    await callback.message.edit_text("❓ Rostan ham xizmatni o'chirmoqchimisiz?", reply_markup=confirm_delete())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_name_"))
async def admin_edit_name(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[3])
    await state.update_data(service_id=service_id, field="name")
    await callback.message.edit_text("📝 Yangi nomni kiriting:")
    await state.set_state(EditServiceStates.get_name)
    await callback.answer()

@router.message(EditServiceStates.get_name)
async def admin_edit_service_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = get_service(data['service_id'])
    new_name = message.text.strip()
    add_service(service['category_id'], new_name, service['api_service_id'], service['admin_price'], service['min'], service['max'])
    await message.answer("✅ Nomi o'zgartirildi!", reply_markup=admin_back())
    await state.clear()

@router.callback_query(F.data.startswith("admin_edit_api_"))
async def admin_edit_api(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[3])
    await state.update_data(service_id=service_id, field="api")
    await callback.message.edit_text("🔢 Yangi API ID ni kiriting:")
    await state.set_state(EditServiceStates.get_api_id)
    await callback.answer()

@router.message(EditServiceStates.get_api_id)
async def admin_edit_service_api(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, son kiriting!")
        return
    data = await state.get_data()
    service = get_service(data['service_id'])
    new_api_id = int(message.text)
    add_service(service['category_id'], service['name'], new_api_id, service['admin_price'], service['min'], service['max'])
    await message.answer("✅ API ID o'zgartirildi!", reply_markup=admin_back())
    await state.clear()

@router.callback_query(F.data.startswith("admin_edit_price_"))
async def admin_edit_price(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[3])
    await state.update_data(service_id=service_id, field="price")
    await callback.message.edit_text("💰 Yangi narxni kiriting (1000 dona uchun so'mda):")
    await state.set_state(EditServiceStates.get_price)
    await callback.answer()

@router.message(EditServiceStates.get_price)
async def admin_edit_service_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text)
    except ValueError:
        await message.answer("❌ Iltimos, son kiriting!")
        return
    data = await state.get_data()
    service = get_service(data['service_id'])
    add_service(service['category_id'], service['name'], service['api_service_id'], new_price, service['min'], service['max'])
    await message.answer(f"✅ Narx o'zgartirildi: {new_price} so'm (1000 dona uchun)", reply_markup=admin_back())
    await state.clear()

# ==================== API DAN IMPORT ====================
@router.callback_query(F.data == "admin_import_services")
async def admin_import(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    await callback.message.edit_text("⏳ API dan xizmatlar import qilinmoqda... Iltimos, kuting...")

    categories_dict, error = await fetch_all_services()
    if error:
        await callback.message.edit_text(f"❌ Import xatosi: {error}", reply_markup=admin_back())
        await callback.answer()
        return

    clear_all_services()
    total_services = 0
    for cat_name, services in categories_dict.items():
        cat_id = add_category(cat_name, cat_name)
        for srv in services:
            price_per_1000 = srv['rate'] * 1000
            add_service(cat_id, srv['name'], srv['service_id'], price_per_1000, srv['min'], srv['max'])
            total_services += 1

    await callback.message.edit_text(
        f"✅ Import muvaffaqiyatli yakunlandi!\n"
        f"📂 {len(categories_dict)} ta kategoriya\n"
        f"📦 {total_services} ta xizmat import qilindi\n"
        f"💰 Narxlar 1000 dona uchun so'mda hisoblandi",
        reply_markup=admin_back()
    )
    await callback.answer()

# ==================== 4. TO'LOVLAR ====================
@router.callback_query(F.data == "admin_payments")
async def admin_payments(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    payments = get_pending_payments()
    if not payments:
        await callback.message.edit_text("💳 Kutilayotgan to'lovlar yo'q.", reply_markup=admin_back())
        return

    text = "💳 Kutilayotgan to'lovlar:\n\n"
    kb = InlineKeyboardBuilder()
    for p in payments:
        text += f"#{p['id']} - @{p['username']} - {p['amount']} so'm - {p['created_at'][:10]}\n"
        kb.button(text=f"📋 #{p['id']}", callback_data=f"admin_pay_view_{p['id']}")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(3)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_pay_view_"))
async def admin_pay_view(callback: types.CallbackQuery):
    payment_id = int(callback.data.split("_")[3])
    payment = get_payment(payment_id)
    if not payment:
        await callback.answer("To'lov topilmadi", show_alert=True)
        return

    await callback.message.edit_text(
        f"💳 To'lov #{payment_id}\n"
        f"👤 Foydalanuvchi: {payment['user_id']}\n"
        f"💰 Summa: {payment['amount']} so'm\n"
        f"📅 Sana: {payment['created_at'][:10]}\n"
        f"📊 Holat: {payment['status']}\n"
        f"📷 Rasm ID: {payment['check_file_id']}",
        reply_markup=payment_actions(payment_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_pay_approve_"))
async def admin_pay_approve(callback: types.CallbackQuery):
    payment_id = int(callback.data.split("_")[3])
    payment = get_payment(payment_id)
    if not payment:
        await callback.answer("To'lov topilmadi", show_alert=True)
        return

    update_payment_status(payment_id, 'approved')
    update_balance(payment['user_id'], payment['amount'])
    await callback.bot.send_message(payment['user_id'], f"✅ To'lov tasdiqlandi! Hisobingizga {payment['amount']} so'm qo'shildi.")
    await callback.message.edit_text("✅ To'lov tasdiqlandi! Balansga qo'shildi.", reply_markup=admin_back())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_pay_reject_"))
async def admin_pay_reject(callback: types.CallbackQuery):
    payment_id = int(callback.data.split("_")[3])
    payment = get_payment(payment_id)
    if not payment:
        await callback.answer("To'lov topilmadi", show_alert=True)
        return

    update_payment_status(payment_id, 'rejected')
    await callback.bot.send_message(payment['user_id'], "❌ To'lov so'rovingiz rad etildi. Iltimos, admin bilan bog'lanib, batafsil ma'lumot oling.")
    await callback.message.edit_text("❌ To'lov bekor qilindi.", reply_markup=admin_back())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_pay_note_"))
async def admin_pay_note(callback: types.CallbackQuery, state: FSMContext):
    payment_id = int(callback.data.split("_")[3])
    await state.update_data(payment_id=payment_id)
    await callback.message.edit_text("📝 Mijozga xabar yozing (izoh):")
    await state.set_state(PaymentNoteStates.get_note)
    await callback.answer()

@router.message(PaymentNoteStates.get_note)
async def send_payment_note(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payment = get_payment(data['payment_id'])
    if payment:
        update_payment_status(data['payment_id'], 'pending', message.text)
        await message.bot.send_message(payment['user_id'], f"📝 Admin xabari: {message.text}")
    await message.answer("✅ Xabar yuborildi!", reply_markup=admin_back())
    await state.clear()

@router.callback_query(F.data.startswith("admin_pay_extra_"))
async def admin_pay_extra(callback: types.CallbackQuery, state: FSMContext):
    payment_id = int(callback.data.split("_")[3])
    await state.update_data(payment_id=payment_id)
    await callback.message.edit_text("➕ Boshqa mablag' miqdorini kiriting (so'm):")
    await state.set_state(PaymentExtraStates.get_amount)
    await callback.answer()

@router.message(PaymentExtraStates.get_amount)
async def pay_extra_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Iltimos, son kiriting!")
        return
    data = await state.get_data()
    payment = get_payment(data['payment_id'])
    if payment:
        update_payment_status(data['payment_id'], 'approved')
        update_balance(payment['user_id'], amount)
        await message.bot.send_message(payment['user_id'], f"✅ Admin tomonidan {amount} so'm qo'shildi!")
    await message.answer(f"✅ {amount} so'm qo'shildi!", reply_markup=admin_back())
    await state.clear()

# ==================== 5. SAVOLLAR ====================
@router.callback_query(F.data == "admin_questions_list")
async def admin_questions_list(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    questions = get_pending_questions()
    if not questions:
        await callback.message.edit_text("❓ Javobsiz savollar yo'q.", reply_markup=admin_back())
        return

    text = "❓ Javobsiz savollar:\n\n"
    kb = InlineKeyboardBuilder()
    for q in questions:
        text += f"#{q['id']} - @{q['username']} - {q['question'][:30]}...\n"
        kb.button(text=f"📝 #{q['id']}", callback_data=f"admin_q_view_{q['id']}")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(3)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_q_view_"))
async def admin_q_view(callback: types.CallbackQuery):
    q_id = int(callback.data.split("_")[3])
    question = None
    for q in get_pending_questions():
        if q['id'] == q_id:
            question = q
            break
    if not question:
        await callback.answer("Savol topilmadi", show_alert=True)
        return

    await callback.message.edit_text(
        f"❓ Savol #{q_id}\n"
        f"👤 @{question['username']}\n"
        f"📝 Savol: {question['question']}\n"
        f"📅 Sana: {question['created_at'][:10]}",
        reply_markup=question_actions(q_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_q_answer_"))
async def admin_q_answer(callback: types.CallbackQuery, state: FSMContext):
    q_id = int(callback.data.split("_")[3])
    await state.update_data(q_id=q_id)
    await callback.message.edit_text("📝 Javobingizni yozing:")
    await state.set_state(AnswerQuestionStates.get_answer)
    await callback.answer()

@router.message(AnswerQuestionStates.get_answer)
async def save_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q_id = data['q_id']
    answer = message.text
    answer_question(q_id, answer)

    for q in get_all_questions():
        if q['id'] == q_id:
            await message.bot.send_message(q['user_id'], f"📨 Savolingizga javob:\n\n{answer}")
            break

    await message.answer("✅ Javob yuborildi!", reply_markup=admin_back())
    await state.clear()

# ==================== 6. KONKURS ====================
@router.callback_query(F.data == "admin_contest")
async def admin_contest(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    contest = get_active_contest()
    text = "🎁 Konkurs boshqaruvi\n\n"
    if contest:
        text += f"📌 Faol: {contest['title']}\n"
        text += f"📅 Tugash: {contest['end_date'][:10]}\n"
        text += f"🏆 1-o'rin: {contest['prize_1']}\n"
        text += f"🏆 2-o'rin: {contest['prize_2']}\n"
        text += f"🏆 3-o'rin: {contest['prize_3']}\n"
    else:
        text += "Hozirda faol konkurs yo'q.\n"

    await callback.message.edit_text(text, reply_markup=contest_admin_actions())
    await callback.answer()

@router.callback_query(F.data == "admin_contest_create")
async def admin_contest_create(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Konkurs sarlavhasini kiriting:")
    await state.set_state(ContestStates.get_title)
    await callback.answer()

@router.message(ContestStates.get_title)
async def contest_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("📝 Konkurs tavsifini kiriting:")
    await state.set_state(ContestStates.get_description)

@router.message(ContestStates.get_description)
async def contest_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("📅 Konkurs necha kundan keyin tugasin? (faqat kun soni):")
    await state.set_state(ContestStates.get_days)

@router.message(ContestStates.get_days)
async def contest_days(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, son kiriting!")
        return
    days = int(message.text)
    data = await state.get_data()
    create_contest(data['title'], data['description'], days)
    await message.answer(f"✅ Konkurs yaratildi!\n📅 {days} kun davom etadi.", reply_markup=admin_back())
    await state.clear()

@router.callback_query(F.data == "admin_contest_prizes")
async def admin_contest_prizes(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🏆 1-o'rin sovg'asini kiriting:")
    await state.set_state(ContestPrizesStates.get_prize1)
    await callback.answer()

@router.message(ContestPrizesStates.get_prize1)
async def contest_prize1(message: types.Message, state: FSMContext):
    await state.update_data(prize1=message.text.strip())
    await message.answer("🏆 2-o'rin sovg'asini kiriting:")
    await state.set_state(ContestPrizesStates.get_prize2)

@router.message(ContestPrizesStates.get_prize2)
async def contest_prize2(message: types.Message, state: FSMContext):
    await state.update_data(prize2=message.text.strip())
    await message.answer("🏆 3-o'rin sovg'asini kiriting:")
    await state.set_state(ContestPrizesStates.get_prize3)

@router.message(ContestPrizesStates.get_prize3)
async def contest_prize3(message: types.Message, state: FSMContext):
    prize3 = message.text.strip()
    data = await state.get_data()
    set_contest_prizes(data['prize1'], data['prize2'], prize3)
    await message.answer(f"✅ Sovg'alar saqlandi!\n🥇 {data['prize1']}\n🥈 {data['prize2']}\n🥉 {prize3}", reply_markup=admin_back())
    await state.clear()

@router.callback_query(F.data == "admin_contest_end")
async def admin_contest_end(callback: types.CallbackQuery):
    contest = get_active_contest()
    if not contest:
        await callback.message.edit_text("❌ Faol konkurs yo'q.", reply_markup=admin_back())
        return

    top_users = get_top_referrers(3)
    text = "🏁 Konkurs tugatildi!\n\n"
    text += f"📌 {contest['title']}\n\n"
    text += "🏆 G'oliblar:\n"
    for i, user in enumerate(top_users, 1):
        u = get_user(user['referrer_id'])
        username = f"@{u['username']}" if u else str(user['referrer_id'])
        prize = contest.get(f'prize_{i}', '')
        text += f"{i}. {username} - {user['count']} ta taklif - Sovg'a: {prize}\n"

    end_contest()

    all_users = get_all_users()
    for u in all_users:
        try:
            await callback.bot.send_message(u['user_id'], f"🎉 Konkurs yakunlandi!\n\n{text}")
        except:
            pass

    await callback.message.edit_text(text, reply_markup=admin_back())
    await callback.answer()

# ==================== 7. XABAR TARQATISH ====================
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    await callback.message.edit_text("📨 Barcha foydalanuvchilarga yuboriladigan xabarni yozing (yoki rasm yuboring):")
    await state.set_state(BroadcastStates.get_message)
    await callback.answer()

@router.message(BroadcastStates.get_message, F.text)
async def broadcast_text(message: types.Message, state: FSMContext):
    await state.update_data(broadcast_text=message.text, broadcast_type="text")
    await message.answer("Xabarni tasdiqlaysizmi?", reply_markup=broadcast_confirm())
    await state.set_state(BroadcastStates.confirm)

@router.message(BroadcastStates.get_message, F.photo)
async def broadcast_photo(message: types.Message, state: FSMContext):
    await state.update_data(broadcast_photo=message.photo[-1].file_id, broadcast_caption=message.caption, broadcast_type="photo")
    await message.answer("Xabarni tasdiqlaysizmi?", reply_markup=broadcast_confirm())
    await state.set_state(BroadcastStates.confirm)

@router.callback_query(F.data == "admin_broadcast_send")
async def broadcast_send(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users = get_all_users()
    sent = 0
    for u in users:
        try:
            if data.get('broadcast_type') == "text":
                await callback.bot.send_message(u['user_id'], data['broadcast_text'])
            elif data.get('broadcast_type') == "photo":
                await callback.bot.send_photo(u['user_id'], data['broadcast_photo'], caption=data.get('broadcast_caption', ''))
            sent += 1
        except:
            pass

    await callback.message.edit_text(f"✅ Xabar {sent} ta foydalanuvchiga yuborildi.", reply_markup=admin_back())
    await state.clear()
    await callback.answer()

# ==================== 8. FOYDALANUVCHILAR ====================
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    users = get_all_users()
    await callback.message.edit_text("👥 Foydalanuvchilar:", reply_markup=users_list(users))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_view_"))
async def admin_user_detail(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[3])
    user = get_user(user_id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    ref_count = get_referral_count(user_id)
    orders = get_user_orders(user_id, 5)

    text = f"👤 Foydalanuvchi: @{user['username'] or user['user_id']}\n"
    text += f"🆔 ID: {user['user_id']}\n"
    text += f"💰 Balans: {user['balance']:.2f} so'm\n"
    text += f"👥 Taklif qilganlar: {ref_count}\n"
    text += f"📅 Qo'shilgan: {user['join_date'][:10]}\n\n"
    text += f"📦 Oxirgi 5 ta buyurtma:\n"
    if orders:
        for o in orders:
            text += f"#{o['id']} - {o['service_name']} - {o['price']:.2f} so'm - {o['status']}\n"
    else:
        text += "Buyurtmalar yo'q.\n"

    await callback.message.edit_text(text, reply_markup=user_profile_actions(user_id))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_add_balance_"))
async def admin_user_add_balance(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[4])
    await state.update_data(target_user_id=user_id)
    await callback.message.edit_text("💰 Qancha mablag' qo'shmoqchisiz? (so'm):")
    await state.set_state(UserBalanceStates.get_amount)
    await callback.answer()

@router.message(UserBalanceStates.get_amount)
async def admin_user_balance_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Iltimos, son kiriting!")
        return
    data = await state.get_data()
    user_id = data['target_user_id']
    update_balance(user_id, amount)
    user = get_user(user_id)
    await message.bot.send_message(user_id, f"💰 Admin tomonidan {amount} so'm qo'shildi! Yangi balans: {user['balance']:.2f} so'm")
    await message.answer(f"✅ {amount} so'm qo'shildi!", reply_markup=admin_back())
    await state.clear()

@router.callback_query(F.data.startswith("admin_user_send_msg_"))
async def admin_user_send_msg(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[4])
    await state.update_data(target_user_id=user_id)
    await callback.message.edit_text("✉️ Foydalanuvchiga yuboriladigan xabarni yozing:")
    await state.set_state(UserMessageStates.get_message)
    await callback.answer()

@router.message(UserMessageStates.get_message)
async def admin_user_send_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['target_user_id']
    try:
        await message.bot.send_message(user_id, f"📩 Admin xabari:\n\n{message.text}")
        await message.answer("✅ Xabar yuborildi!", reply_markup=admin_back())
    except:
        await message.answer("❌ Xabar yuborib bo'lmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).", reply_markup=admin_back())
    await state.clear()

# ==================== 9. KARTA MA'LUMOTLARI ====================
@router.callback_query(F.data == "admin_card")
async def admin_card(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return

    card = get_card()
    if card:
        text = f"💳 Karta ma'lumotlari:\n\n"
        text += f"🔢 Raqam: {card['card_number']}\n"
        text += f"👤 Ism: {card['full_name']}\n"
        text += f"📅 Yangilangan: {card['updated_at'][:10]}"
    else:
        text = "💳 Karta ma'lumotlari kiritilmagan."

    await callback.message.edit_text(text, reply_markup=card_actions())
    await callback.answer()

@router.callback_query(F.data == "admin_card_edit")
async def admin_card_edit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔢 Karta raqamini kiriting (16 raqam, bo'sh joysiz):")
    await state.set_state(CardStates.get_card_number)
    await callback.answer()

@router.message(CardStates.get_card_number)
async def card_number(message: types.Message, state: FSMContext):
    card_num = message.text.strip().replace(" ", "")
    if not card_num.isdigit() or len(card_num) != 16:
        await message.answer("❌ Iltimos, 16 xonali raqam kiriting (masalan: 8600123456789012):")
        return
    await state.update_data(card_number=card_num)
    await message.answer("👤 Ism va familyani kiriting (masalan: Ivanov I.I.):")
    await state.set_state(CardStates.get_full_name)

@router.message(CardStates.get_full_name)
async def card_full_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    if not full_name:
        await message.answer("❌ Ism-familya bo'sh bo'lishi mumkin emas!")
        return
    data = await state.get_data()
    save_card(data['card_number'], full_name)
    await message.answer(f"✅ Karta ma'lumotlari saqlandi!\n🔢 {data['card_number']}\n👤 {full_name}", reply_markup=admin_back())
    await state.clear()

# ==================== BOSH MENYUDAN ADMIN PANELGA TUGMA ====================
@router.callback_query(F.data == "admin_panel_btn")
async def admin_panel_btn(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    await callback.message.edit_text("🔧 Admin paneli", reply_markup=admin_menu())
    await callback.answer()