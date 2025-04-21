import telebot
from telebot import types
import sqlite3
import time
import os

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("trk_bot.db", check_same_thread=False)
cursor = db.cursor()

user_states = {}

def get_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💼 Баланс", "🏦 Инвестировать")
    kb.row("🎮 Игры", "🧑‍🤝‍🧑 Пригласить друга")
    kb.row("💸 Вывести", "📊 Моя статистика")
    return kb

def get_back_markup():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("↩️ Назад")
    return kb

@bot.message_handler(func=lambda m: m.text == "↩️ Назад")
def back_to_menu(msg):
    bot.send_message(msg.chat.id, "Вы вернулись в главное меню:", reply_markup=get_main_menu())
  @bot.message_handler(commands=['start'])
def start(msg):
    user_id = str(msg.from_user.id)
    username = msg.from_user.username or ""
    ip = str(msg.chat.id)  # IP можно подставить, если будет реальный IP

    # Рефералка (если передан ?start=ref123456)
    args = msg.text.split()
    ref = None
    if len(args) > 1 and args[1].startswith("ref"):
        ref = args[1][3:]

    # Регистрация пользователя
    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (tg_id, username, ip, referrer) VALUES (?, ?, ?, ?)",
                       (user_id, username, ip, ref))
        db.commit()
        if ref:
            cursor.execute("INSERT INTO referrals (user_id, invited_id, time) VALUES (?, ?, ?)",
                           (ref, user_id, int(time.time())))
            cursor.execute("UPDATE users SET balance = balance + 1 WHERE tg_id = ?", (ref,))
            db.commit()
            bot.send_message(int(ref), "Вы получили +1 USDT за приглашённого друга!")

    bot.send_message(msg.chat.id,
        "👋 Добро пожаловать в *TRK-Бот*!\n\n"
        "📈 Здесь ты можешь *инвестировать*, *играть* и *зарабатывать* USDT каждый день.\n"
        "Выбирай раздел ниже и начни зарабатывать прямо сейчас.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💼 Баланс")
def balance(msg):
    user_id = str(msg.from_user.id)
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (user_id,))
    result = cursor.fetchone()
    balance = result[0] if result else 0
    bot.send_message(msg.chat.id, f"💼 Ваш баланс: {balance:.2f} USDT", reply_markup=get_back_markup())
  @bot.message_handler(func=lambda m: m.text == "🏦 Инвестировать")
def invest_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📈 Вложить 150$", "📈 Вложить 350$")
    kb.row("📈 Вложить 750$", "📊 Мои инвестиции")
    kb.add("↩️ Назад")
    bot.send_message(msg.chat.id, 
        "*Инвестируй и зарабатывай с TRK:*\n\n"
        "• 150$ → 4$/день (75 дней)\n"
        "• 350$ → 9$/день (75 дней)\n"
        "• 750$ → 25$/день (75 дней)\n\n"
        "💰 Доход поступает на баланс каждый день.",
        reply_markup=kb,
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in ["📈 Вложить 150$", "📈 Вложить 350$", "📈 Вложить 750$"])
def process_invest(msg):
    user_id = str(msg.from_user.id)
    amount = int(msg.text.split()[1].replace("$", ""))
    plans = {150: 4, 350: 9, 750: 25}
    daily = plans[amount]
    duration = 75 * 86400  # 75 дней

    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (user_id,))
    bal = cursor.fetchone()[0]
    if bal < amount:
        bot.send_message(msg.chat.id, "❌ Недостаточно средств.", reply_markup=get_main_menu())
        return

    now = int(time.time())
    cursor.execute("UPDATE users SET balance = balance - ? WHERE tg_id = ?", (amount, user_id))
    cursor.execute("INSERT INTO investments (user_id, amount, daily_income, start_time) VALUES (?, ?, ?, ?)",
                   (user_id, amount, daily, now))
    db.commit()

    bot.send_message(msg.chat.id, f"✅ Вы вложили {amount}$ — получаете {daily}$/день в течение 75 дней.",
                     reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "📊 Мои инвестиции")
def my_investments(msg):
    user_id = str(msg.from_user.id)
    cursor.execute("SELECT amount, daily_income, start_time FROM investments WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "У вас нет активных инвестиций.", reply_markup=get_main_menu())
        return

    text = "📊 Ваши инвестиции:\n\n"
    now = int(time.time())
    for amount, daily, start in rows:
        days_passed = (now - start) // 86400
        days_left = max(0, 75 - days_passed)
        text += f"• {amount}$ → {daily}$/день\n   Осталось дней: {days_left}\n\n"

    bot.send_message(msg.chat.id, text, reply_markup=get_back_markup())
  @bot.message_handler(func=lambda m: m.text == "🎮 Игры")
def game_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎯 Угадай число", "⚖️ Чёт / Нечёт")
    kb.row("✂️ КНБ", "↩️ Назад")
    bot.send_message(msg.chat.id, 
        "*Выберите игру:*\n\n"
        "🎯 Угадай число — ставка 1$, выигрыш 2$\n"
        "⚖️ Чёт / Нечёт — ставка 1$, выигрыш 1.9$\n"
        "✂️ КНБ — ставка 1$, выигрыш 1.75$\n\n"
        "⚠️ Шанс выигрыша — ~40%",
        reply_markup=kb,
        parse_mode="Markdown")
  @bot.message_handler(func=lambda m: m.text == "🎯 Угадай число")
def guess_number_start(msg):
    user_id = str(msg.from_user.id)
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    if balance < 1:
        bot.send_message(msg.chat.id, "Недостаточно средств.")
        return

    user_states[user_id] = "guess_number"
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, 6):
        kb.add(str(i))
    kb.add("↩️ Назад")
    bot.send_message(msg.chat.id, "Я загадал число от 1 до 5. Угадай!", reply_markup=kb)

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) == "guess_number")
def guess_number_check(msg):
    user_id = str(msg.from_user.id)
    try:
        number = int(msg.text)
        if number < 1 or number > 5:
            raise ValueError
    except:
        bot.send_message(msg.chat.id, "Введите число от 1 до 5.")
        return

    import random
    cursor.execute("UPDATE users SET balance = balance - 1 WHERE tg_id = ?", (user_id,))
    win = random.random() <= 0.4

    if win:
        cursor.execute("UPDATE users SET balance = balance + 2 WHERE tg_id = ?", (user_id,))
        bot.send_message(msg.chat.id, "Поздравляем! Вы угадали! +2$")
    else:
        bot.send_message(msg.chat.id, "Вы не угадали.")

    db.commit()
    user_states.pop(user_id)
  @bot.message_handler(func=lambda m: m.text == "⚖️ Чёт / Нечёт")
def even_odd_start(msg):
    user_id = str(msg.from_user.id)
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    if balance < 1:
        bot.send_message(msg.chat.id, "Недостаточно средств для ставки.")
        return

    user_states[user_id] = "even_odd"
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Чёт", "Нечёт")
    kb.add("↩️ Назад")
    bot.send_message(msg.chat.id, "Выберите: Чёт или Нечёт", reply_markup=kb)

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) == "even_odd")
def even_odd_check(msg):
    user_id = str(msg.from_user.id)
    choice = msg.text.lower()
    if choice not in ["чёт", "нечёт"]:
        bot.send_message(msg.chat.id, "Выберите Чёт или Нечёт.")
        return

    import random
    cursor.execute("UPDATE users SET balance = balance - 1 WHERE tg_id = ?", (user_id,))
    win = random.random() <= 0.4

    if win:
        cursor.execute("UPDATE users SET balance = balance + 1.9 WHERE tg_id = ?", (user_id,))
        bot.send_message(msg.chat.id, f"Вы выиграли! +1.9$")
    else:
        bot.send_message(msg.chat.id, "Вы проиграли.")

    db.commit()
    user_states.pop(user_id)
  @bot.message_handler(func=lambda m: m.text == "✂️ КНБ")
def rps_start(msg):
    user_id = str(msg.from_user.id)
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    if balance < 1:
        bot.send_message(msg.chat.id, "Недостаточно средств.")
        return

    user_states[user_id] = "rps"
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Камень", "Ножницы", "Бумага")
    kb.add("↩️ Назад")
    bot.send_message(msg.chat.id, "Выберите:", reply_markup=kb)

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) == "rps")
def rps_check(msg):
    user_id = str(msg.from_user.id)
    user = msg.text.lower()
    options = ["камень", "ножницы", "бумага"]
    if user not in options:
        bot.send_message(msg.chat.id, "Выберите: Камень, Ножницы или Бумага.")
        return

    import random
    bot_choice = random.choice(options)
    win = random.random() <= 0.4

    cursor.execute("UPDATE users SET balance = balance - 1 WHERE tg_id = ?", (user_id,))
    if win:
        cursor.execute("UPDATE users SET balance = balance + 1.75 WHERE tg_id = ?", (user_id,))
        bot.send_message(msg.chat.id, f"Бот выбрал: {bot_choice}\nВы выиграли 1.75$")
    else:
        bot.send_message(msg.chat.id, f"Бот выбрал: {bot_choice}\nВы проиграли.")

    db.commit()
    user_states.pop(user_id)
  @bot.message_handler(func=lambda m: m.text == "📊 Моя статистика")
def show_stats(msg):
    user_id = str(msg.from_user.id)

    # Баланс
    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    # Игры
    cursor.execute("SELECT COUNT(*), SUM(win), SUM(amount) FROM games WHERE user_id = ?", (user_id,))
    game_data = cursor.fetchone()
    total_games = game_data[0] or 0
    wins = game_data[1] or 0
    total_spent = game_data[2] or 0

    # Инвестиции
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM investments WHERE user_id = ?", (user_id,))
    invest_data = cursor.fetchone()
    total_invests = invest_data[0] or 0
    invested_sum = invest_data[1] or 0

    # Рефералы
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE user_id = ?", (user_id,))
    ref_count = cursor.fetchone()[0] or 0

    text = (
        f"📊 Ваша статистика:\n\n"
        f"Баланс: {balance:.2f} USDT\n"
        f"Сыграно игр: {total_games}\n"
        f"Побед: {wins}\n"
        f"Потрачено на игры: {total_spent or 0:.2f} USDT\n"
        f"Инвестировано: {total_invests} на сумму {invested_sum or 0:.2f} USDT\n"
        f"Приглашено по ссылке: {ref_count}"
    )
    bot.send_message(msg.chat.id, text, reply_markup=get_back_markup())
  @bot.message_handler(func=lambda m: m.text == "💸 Вывести")
def request_withdraw(msg):
    user_states[str(msg.from_user.id)] = "awaiting_withdraw"
    bot.send_message(msg.chat.id, "Введите сумму и TRC20-кошелёк через пробел (например: 30 TNk...):",
                     reply_markup=get_back_markup())

@bot.message_handler(func=lambda m: user_states.get(str(m.from_user.id)) == "awaiting_withdraw")
def process_withdraw(msg):
    user_id = str(msg.from_user.id)
    ip = str(msg.chat.id)
    try:
        amount_str, wallet = msg.text.strip().split()
        amount = float(amount_str)
    except:
        bot.send_message(msg.chat.id, "❌ Неверный формат. Пример: 30 TXXXXXXXX", reply_markup=get_back_markup())
        return

    cursor.execute("SELECT COUNT(*) FROM withdrawals WHERE wallet = ?", (wallet,))
    if cursor.fetchone()[0] > 0:
        bot.send_message(msg.chat.id, "❌ Этот кошелёк уже использовался.", reply_markup=get_back_markup())
        return

    cursor.execute("SELECT ip FROM users WHERE tg_id = ?", (user_id,))
    user_ip = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE ip = ?", (user_ip,))
    if cursor.fetchone()[0] > 1:
        bot.send_message(msg.chat.id, "❌ С одного устройства нельзя создавать несколько аккаунтов.",
                         reply_markup=get_back_markup())
        return

    cursor.execute("SELECT balance FROM users WHERE tg_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    if balance < amount:
        bot.send_message(msg.chat.id, "❌ Недостаточно средств.", reply_markup=get_back_markup())
        return
    if amount < 25:
        bot.send_message(msg.chat.id, "Минимальная сумма вывода — 25 USDT.", reply_markup=get_back_markup())
        return

    cursor.execute("UPDATE users SET balance = balance - ? WHERE tg_id = ?", (amount, user_id))
    cursor.execute("INSERT INTO withdrawals (user_id, amount, wallet, time) VALUES (?, ?, ?, ?)",
                   (user_id, amount, wallet, int(time.time())))
    db.commit()

    bot.send_message(msg.chat.id, f"✅ Запрос на вывод {amount}$ принят. Выплата в течение 24 часов.",
                     reply_markup=get_main_menu())
    user_states.pop(user_id)
  @bot.message_handler(func=lambda m: m.text == "🧑‍🤝‍🧑 Пригласить друга")
def invite_friend(msg):
    user_id = str(msg.from_user.id)
    username = bot.get_me().username
    link = f"https://t.me/{username}?start=ref{user_id}"
    
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE user_id = ?", (user_id,))
    invited = cursor.fetchone()[0]

    text = (
        f"Ваша реферальная ссылка:\n{link}\n\n"
        f"Вы пригласили: {invited} пользователей\n"
        f"Бонус: +1 USDT за каждого активного приглашённого"
    )

    bot.send_message(msg.chat.id, text, reply_markup=get_back_markup())
  print("🤖 Бот TRK запущен...")
bot.polling(none_stop=True)
