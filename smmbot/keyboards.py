from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_IDS

# ==================== USER MENU ====================
def main_menu(user_id=None):
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Xizmatlar", callback_data="menu_services")
    kb.button(text="⭐ Sevimlilar", callback_data="menu_favorites")
    kb.button(text="🎁 Konkurs", callback_data="menu_contest")
    kb.button(text="📊 Buyurtma holati", callback_data="menu_status")
    kb.button(text="📜 Buyurtma tarixi", callback_data="menu_history")
    kb.button(text="👤 Mening hisobim", callback_data="menu_account")
    kb.button(text="💳 Balansni to'ldirish", callback_data="menu_refill")
    kb.button(text="👥 Do'stni taklif qilish", callback_data="menu_referral")
    kb.button(text="📞 Admin bilan aloqa", callback_data="menu_contact")
    kb.button(text="❓ Savollar", callback_data="menu_questions")
    
    # Admin uchun maxsus tugma
    if user_id and user_id in ADMIN_IDS:
        kb.button(text="🔧 Admin panel", callback_data="admin_panel_btn")
    
    kb.adjust(2)
    return kb.as_markup()

def back_to_main():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Orqaga", callback_data="back_main")
    return kb.as_markup()

# ==================== ADMIN MENU ====================
def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Statistika", callback_data="admin_stats")
    kb.button(text="📦 Barcha buyurtmalar", callback_data="admin_orders")
    kb.button(text="📂 Kategoriya va Xizmatlar", callback_data="admin_categories")
    kb.button(text="💳 To'lovlar", callback_data="admin_payments")
    kb.button(text="❓ Savollar", callback_data="admin_questions_list")
    kb.button(text="🎁 Konkurs boshqaruvi", callback_data="admin_contest")
    kb.button(text="📨 Xabar tarqatish", callback_data="admin_broadcast")
    kb.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
    kb.button(text="💳 Karta ma'lumotlari", callback_data="admin_card")
    kb.adjust(2)
    return kb.as_markup()

def admin_back():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Admin menyuga", callback_data="admin_back")
    return kb.as_markup()

# ==================== KATEGORIYA VA XIZMATLAR (ADMIN UCHUN) ====================
def categories_list(categories):
    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=f"📂 {cat['name']}", callback_data=f"admin_cat_view_{cat['id']}")
        kb.button(text="🗑️", callback_data=f"admin_cat_del_{cat['id']}")
    kb.button(text="➕ Yangi kategoriya qo'shish", callback_data="admin_add_category")
    kb.button(text="🔄 API dan import qilish", callback_data="admin_import_services")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(2)
    return kb.as_markup()

def services_list(services, category_id):
    kb = InlineKeyboardBuilder()
    if services:
        for srv in services:
            text = f"{srv['name']} ({srv['admin_price']} so'm/1000 dona)"
            kb.button(text=text, callback_data=f"admin_srv_view_{srv['id']}")
            kb.button(text="✏️", callback_data=f"admin_srv_edit_{srv['id']}")
            kb.button(text="🗑️", callback_data=f"admin_srv_del_{srv['id']}")
    kb.button(text="➕ Yangi xizmat qo'shish", callback_data=f"admin_add_service_{category_id}")
    kb.button(text="🔙 Kategoriyalarga", callback_data="admin_categories")
    kb.adjust(3)
    return kb.as_markup()

def confirm_delete():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chir", callback_data="admin_confirm_delete_yes")
    kb.button(text="❌ Bekor qil", callback_data="admin_confirm_delete_no")
    return kb.as_markup()

def edit_service_buttons(service_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Nomni o'zgartirish", callback_data=f"admin_edit_name_{service_id}")
    kb.button(text="🔢 API ID ni o'zgartirish", callback_data=f"admin_edit_api_{service_id}")
    kb.button(text="💰 Narxni o'zgartirish", callback_data=f"admin_edit_price_{service_id}")
    kb.button(text="🔙 Orqaga", callback_data=f"admin_back_services_{service_id}")
    kb.adjust(1)
    return kb.as_markup()

# ==================== USER XIZMAT TUGMALARI ====================
def user_service_buttons(service_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="❤️ Sevimlilarga qo'shish", callback_data=f"user_add_fav_{service_id}")
    kb.button(text="🛒 Buyurtma berish", callback_data=f"user_order_now_{service_id}")
    kb.button(text="🔙 Orqaga", callback_data="user_back_services")
    kb.adjust(1)
    return kb.as_markup()

# ==================== BUYURTMA (USER) ====================
def confirm_order():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, tasdiqlayman", callback_data="user_confirm_order")
    kb.button(text="❌ Bekor qilish", callback_data="user_cancel_order")
    kb.adjust(2)
    return kb.as_markup()

# ==================== TO'LOVLAR (ADMIN) ====================
def payment_actions(payment_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"admin_pay_approve_{payment_id}")
    kb.button(text="❌ Bekor qilish", callback_data=f"admin_pay_reject_{payment_id}")
    kb.button(text="📝 Xabar yozish", callback_data=f"admin_pay_note_{payment_id}")
    kb.button(text="➕ Boshqa mablag' qo'shish", callback_data=f"admin_pay_extra_{payment_id}")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(2)
    return kb.as_markup()

# ==================== SAVOLLAR (ADMIN) ====================
def question_actions(q_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Javob yozish", callback_data=f"admin_q_answer_{q_id}")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    return kb.as_markup()

def user_questions_list():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yangi savol qo'shish", callback_data="user_add_question")
    kb.button(text="🔙 Orqaga", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

# ==================== KONKURS (ADMIN) ====================
def contest_admin_actions():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yangi konkurs", callback_data="admin_contest_create")
    kb.button(text="🏆 Sovg'alarni belgilash", callback_data="admin_contest_prizes")
    kb.button(text="⏹️ Konkursni tugatish", callback_data="admin_contest_end")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()

# ==================== FOYDALANUVCHILAR (ADMIN) ====================
def user_profile_actions(user_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Balans qo'shish", callback_data=f"admin_user_add_balance_{user_id}")
    kb.button(text="✉️ Xabar yuborish", callback_data=f"admin_user_send_msg_{user_id}")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()

def users_list(users):
    kb = InlineKeyboardBuilder()
    for u in users:
        kb.button(text=f"👤 {u['username'] or u['user_id']} ({u['balance']} so'm)", 
                  callback_data=f"admin_user_view_{u['user_id']}")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()

# ==================== KARTA (ADMIN) ====================
def card_actions():
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ O'zgartirish", callback_data="admin_card_edit")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()

# ==================== BROADCAST (ADMIN) ====================
def broadcast_confirm():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Yuborish", callback_data="admin_broadcast_send")
    kb.button(text="❌ Bekor qilish", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()

# ==================== ORQA QAYTISH UNIVERSAL ====================
def back_button(callback_data="back_main"):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Orqaga", callback_data=callback_data)
    return kb.as_markup()