import sqlite3

db = sqlite3.connect("trk_bot.db", check_same_thread=False)
cursor = db.cursor()

# Таблица пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id TEXT UNIQUE,
    username TEXT,
    ip TEXT,
    wallet TEXT,
    balance REAL DEFAULT 0,
    referrer TEXT
)
""")

# Инвестиции
cursor.execute("""
CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    amount REAL,
    daily_income REAL,
    start_time INTEGER
)
""")

# Игры
cursor.execute("""
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    game TEXT,
    win INTEGER,
    amount REAL,
    time INTEGER
)
""")

# Выводы
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    amount REAL,
    wallet TEXT,
    time INTEGER
)
""")

# Рефералы
cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    invited_id TEXT,
    time INTEGER
)
""")

db.commit()
print("✅ База данных создана")
