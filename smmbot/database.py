import sqlite3
import datetime

DB_NAME = "smm_bot.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0,
            referrer_id INTEGER,
            join_date TEXT
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            api_category_name TEXT
        );
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT,
            api_service_id INTEGER UNIQUE,
            admin_price REAL,
            min INTEGER,
            max INTEGER,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_id INTEGER,
            link TEXT,
            quantity INTEGER,
            price REAL,
            status TEXT,
            api_order_id INTEGER,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(service_id) REFERENCES services(id)
        );
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            service_id INTEGER,
            PRIMARY KEY(user_id, service_id)
        );
        CREATE TABLE IF NOT EXISTS referrals (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            bonus_earned REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS contests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            prize_1 TEXT,
            prize_2 TEXT,
            prize_3 TEXT,
            is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            check_file_id TEXT,
            status TEXT DEFAULT 'pending',
            admin_note TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            answer TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS admin_card (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            full_name TEXT,
            updated_at TEXT
        );
    ''')
    conn.commit()
    conn.close()
    print("✅ Barcha jadvallar yaratildi")

# ==================== KATEGORIYA VA XIZMATLAR ====================
def clear_all_services():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM services")
    conn.commit()
    conn.close()

def add_category(name, api_name=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categories (name, api_category_name) VALUES (?, ?)", (name, api_name or name))
    conn.commit()
    row = cur.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()
    conn.close()
    return row['id'] if row else None

def add_service(category_id, name, api_service_id, admin_price, min_q, max_q):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO services (category_id, name, api_service_id, admin_price, min, max)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (category_id, name, api_service_id, admin_price, min_q, max_q))
    conn.commit()
    conn.close()

def get_category_by_api_name(api_name):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT id FROM categories WHERE api_category_name=?", (api_name,)).fetchone()
    conn.close()
    return row['id'] if row else None

def get_all_categories():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return rows

def get_services_by_category(cat_id):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM services WHERE category_id=? ORDER BY name", (cat_id,)).fetchall()
    conn.close()
    return rows

def get_service(service_id):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM services WHERE id=?", (service_id,)).fetchone()
    conn.close()
    return row

def get_service_by_api_id(api_id):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM services WHERE api_service_id=?", (api_id,)).fetchone()
    conn.close()
    return row

def delete_category(cat_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()

def delete_service(service_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM services WHERE id=?", (service_id,))
    conn.commit()
    conn.close()

# ==================== FOYDALANUVCHILAR (USERNAME YANGILANADI) ====================
def add_user(user_id, username, full_name, referrer_id=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (user_id, username, full_name, referrer_id, join_date)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
    ''', (user_id, username, full_name, referrer_id, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row

def update_balance(user_id, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("SELECT user_id, username, balance FROM users ORDER BY user_id DESC LIMIT 20").fetchall()
    conn.close()
    return rows

def get_user_by_username(username):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row

# ==================== BUYURTMALAR ====================
def add_order(user_id, service_id, link, quantity, price, api_order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO orders (user_id, service_id, link, quantity, price, status, api_order_id, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    ''', (user_id, service_id, link, quantity, price, 'Pending', api_order_id, datetime.datetime.now().isoformat()))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(user_id, limit=20):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT o.*, s.name as service_name 
        FROM orders o 
        JOIN services s ON o.service_id=s.id 
        WHERE o.user_id=? 
        ORDER BY o.id DESC LIMIT ?
    ''', (user_id, limit)).fetchall()
    conn.close()
    return rows

def get_user_active_orders(user_id):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT o.*, s.name as service_name 
        FROM orders o 
        JOIN services s ON o.service_id=s.id 
        WHERE o.user_id=? AND o.status IN ('Pending', 'Processing')
        ORDER BY o.id DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return rows

def get_order(order_id):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    return row

def update_order_status(order_id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

def get_all_orders(limit=20):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT o.*, u.username, s.name as service_name 
        FROM orders o 
        JOIN users u ON o.user_id = u.user_id
        JOIN services s ON o.service_id = s.id
        ORDER BY o.id DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return rows

# ==================== SEVIMLILAR ====================
def add_favorite_db(user_id, service_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO favorites (user_id, service_id) VALUES (?,?)", (user_id, service_id))
    conn.commit()
    conn.close()

def remove_favorite_db(user_id, service_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM favorites WHERE user_id=? AND service_id=?", (user_id, service_id))
    conn.commit()
    conn.close()
def get_favorites(user_id):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT s.* FROM favorites f 
        JOIN services s ON f.service_id=s.id 
        WHERE f.user_id=?
    ''', (user_id,)).fetchall()
    conn.close()
    return rows

# ==================== REFERALLAR ====================
def save_referral(user_id, referrer_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO referrals (user_id, referrer_id) VALUES (?,?)", (user_id, referrer_id))
    conn.commit()
    conn.close()

def get_referral_count(user_id):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,)).fetchone()
    conn.close()
    return row[0] if row else 0

def get_total_referrals():
    """Barcha takliflar soni (konkurs uchun)"""
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT COUNT(*) FROM referrals").fetchone()
    conn.close()
    return row[0] if row else 0

def get_top_referrers(limit=3):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT referrer_id, COUNT(*) as count 
        FROM referrals 
        GROUP BY referrer_id 
        ORDER BY count DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return rows

# ==================== TO'LOVLAR ====================
def add_payment(user_id, amount, file_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO payments (user_id, amount, check_file_id, created_at)
        VALUES (?,?,?,?)
    ''', (user_id, amount, file_id, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_pending_payments():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT p.*, u.username FROM payments p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.status = 'pending' ORDER BY p.id DESC
    ''').fetchall()
    conn.close()
    return rows

def update_payment_status(payment_id, status, admin_note=None):
    conn = get_db()
    cur = conn.cursor()
    if admin_note:
        cur.execute("UPDATE payments SET status=?, admin_note=? WHERE id=?", (status, admin_note, payment_id))
    else:
        cur.execute("UPDATE payments SET status=? WHERE id=?", (status, payment_id))
    conn.commit()
    conn.close()

def get_payment(payment_id):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
    conn.close()
    return row

def get_all_payments(limit=20):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT p.*, u.username FROM payments p
        JOIN users u ON p.user_id = u.user_id
        ORDER BY p.id DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return rows

# ==================== SAVOLLAR ====================
def add_question(user_id, question):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO questions (user_id, question, created_at)
        VALUES (?,?,?)
    ''', (user_id, question, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_questions(user_id):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM questions WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    conn.close()
    return rows

def get_pending_questions():
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT q.*, u.username FROM questions q
        JOIN users u ON q.user_id = u.user_id
        WHERE q.status = 'pending' ORDER BY q.id DESC
    ''').fetchall()
    conn.close()
    return rows

def answer_question(q_id, answer):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE questions SET answer=?, status='answered' WHERE id=?", (answer, q_id))
    conn.commit()
    conn.close()

def get_all_questions(limit=20):
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT q.*, u.username FROM questions q
        JOIN users u ON q.user_id = u.user_id
        ORDER BY q.id DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return rows

# ==================== KONKURS ====================
def get_active_contest():
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM contests WHERE is_active=1 ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return row

def create_contest(title, desc, days):
    conn = get_db()
    cur = conn.cursor()
    end_date = (datetime.datetime.now() + datetime.timedelta(days=int(days))).isoformat()
    cur.execute('''
        INSERT INTO contests (title, description, start_date, end_date, is_active)
        VALUES (?,?,?,?,1)
    ''', (title, desc, datetime.datetime.now().isoformat(), end_date))
    conn.commit()
    conn.close()

def set_contest_prizes(prize1, prize2, prize3):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE contests SET prize_1=?, prize_2=?, prize_3=? WHERE is_active=1 ORDER BY id DESC LIMIT 1", 
                (prize1, prize2, prize3))
    conn.commit()
    conn.close()

def end_contest():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE contests SET is_active=0 WHERE is_active=1")
    conn.commit()
    conn.close()

# ==================== KARTA ====================
def get_card():
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM admin_card LIMIT 1").fetchone()
    conn.close()
    return row

def save_card(number, full_name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM admin_card")  # Faqat bitta yozuv bo'ladi
    cur.execute("INSERT INTO admin_card (card_number, full_name, updated_at) VALUES (?,?,?)", 
                (number, full_name, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()