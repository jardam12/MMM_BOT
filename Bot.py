import telebot
from telebot import types
import json
import time
import os
import threading
import requests
import random

TOKEN = '7017412513:AAGckA2FKxQtlSFSn6-XsIpIBjDISwJt2W0'
bot = telebot.TeleBot(TOKEN)

BALANCE_FILE = 'balances.json'
INVEST_FILE = 'investments.json'
PAYMENTS_FILE = 'payments.json'
REFERRALS_FILE = 'referrals.json'
ADMINS_FILE = 'admins.json'
GAMES_FILE = 'games.json'
LEVELS_FILE = 'levels.json'

for file in [BALANCE_FILE, INVEST_FILE, PAYMENTS_FILE, REFERRALS_FILE, ADMINS_FILE, GAMES_FILE, LEVELS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)

user_states = {}
game_states = {}

main_menu_buttons = [
    "Баланс", "Пополнить", "Вывести",
    "Инвестировать", "Пригласить друга",
    "Игры", "Моя статистика"
]

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for btn in main_menu_buttons:
        markup.add(types.KeyboardButton(btn))
    return markup
@bot.message_handler(commands=['start'])
def handle_start(message):
    args = message.text.split()
    user_id = str(message.from_user.id)

    balances = load_json(BALANCE_FILE)
    referrals = load_json(REFERRALS_FILE)

    if user_id not in balances:
        balances[user_id] = 100
        if len(args) == 2 and args[1].startswith("ref"):
            ref_id = args[1][3:]
            if ref_id != user_id and ref_id not in referrals.get(user_id, []):
                balances[ref_id] = balances.get(ref_id, 0) + 1
                referrals[user_id] = ref_id
                save_json(BALANCE_FILE, balances)
                save_json(REFERRALS_FILE, referrals)
                bot.send_message(int(ref_id), f"Вы получили 1 USDT за приглашённого пользователя!")

    save_json(BALANCE_FILE, balances)
    bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "Баланс")
def balance(msg):
    user_id = str(msg.from_user.id)
    balances = load_json(BALANCE_FILE)
    bot.send_message(msg.chat.id, f"Ваш баланс: {balances.get(user_id, 0)} USDT")

@bot.message_handler(func=lambda msg: msg.text == "Пополнить")
def deposit(msg):
    user_states[str(msg.from_user.id)] = "awaiting_deposit"
    bot.send_message(msg.chat.id, "Введите сумму для пополнения:")

@bot.message_handler(func=lambda msg: msg.text == "Вывести")
def withdraw(msg):
    user_states[str(msg.from_user.id)] = "awaiting_withdraw"
    bot.send_message(msg.chat.id, "Введите сумму и TRC20 кошелёк через пробел:")

@bot.message_handler(func=lambda msg: msg.text == "Инвестировать")
def invest_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Вложить 150$", "Вложить 300$", "Вложить 700$")
    bot.send_message(msg.chat.id, "Выберите инвестиционный план:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "Игры")
def games(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Угадай число", "Авиатор", "Камень-Ножницы-Бумага")
    bot.send_message(msg.chat.id, "Выберите игру:", reply_markup=markup)
@bot.message_handler(func=lambda msg: msg.text in ["Угадай число", "Авиатор", "Камень-Ножницы-Бумага"])
def handle_games(msg):
    user_id = str(msg.from_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(user_id, 0)

    if balance < 1:
        bot.send_message(msg.chat.id, "Недостаточно средств для игры. Нужно минимум 1 USDT.")
        return

    balances[user_id] -= 1
    save_json(BALANCE_FILE, balances)

    if msg.text == "Угадай число":
        game_states[user_id] = "guess"
        bot.send_message(msg.chat.id, "Я загадал число от 1 до 8. Угадай!")

    elif msg.text == "Авиатор":
        lose = random.random() < 0.8
        if lose:
            bot.send_message(msg.chat.id, "Вы проиграли! Самолёт не взлетел.")
        else:
            balances[user_id] += 2
            save_json(BALANCE_FILE, balances)
            bot.send_message(msg.chat.id, "Поздравляем! Вы выиграли 2 USDT в авиаторе!")

    elif msg.text == "Камень-Ножницы-Бумага":
        game_states[user_id] = "rps"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Камень", "Ножницы", "Бумага")
        bot.send_message(msg.chat.id, "Выбери: Камень, Ножницы или Бумага", reply_markup=markup)

@bot.message_handler(func=lambda msg: game_states.get(str(msg.from_user.id)) == "guess")
def guess_number(msg):
    user_id = str(msg.from_user.id)
    try:
        choice = int(msg.text)
    except:
        bot.send_message(msg.chat.id, "Нужно ввести число от 1 до 8.")
        return

    if choice < 1 or choice > 8:
        bot.send_message(msg.chat.id, "Число должно быть от 1 до 8.")
        return

    win = random.randint(1, 8)
    if choice == win:
        balances = load_json(BALANCE_FILE)
        balances[user_id] += 2
        save_json(BALANCE_FILE, balances)
        bot.send_message(msg.chat.id, f"Вы угадали! Это было {win}. Вы выиграли 2 USDT!")
    else:
        bot.send_message(msg.chat.id, f"Неверно! Я загадал {win}. Вы проиграли.")
    game_states.pop(user_id)

@bot.message_handler(func=lambda msg: game_states.get(str(msg.from_user.id)) == "rps")
def rock_paper_scissors(msg):
    user_id = str(msg.from_user.id)
    user_choice = msg.text.lower()
    if user_choice not in ["камень", "ножницы", "бумага"]:
        bot.send_message(msg.chat.id, "Выберите: Камень, Ножницы или Бумага")
        return

    bot_choice = random.choice(["камень", "ножницы", "бумага"])
    result = None
    if user_choice == bot_choice:
        result = "Ничья!"
    elif (user_choice == "камень" and bot_choice == "ножницы") or \
         (user_choice == "ножницы" and bot_choice == "бумага") or \
         (user_choice == "бумага" and bot_choice == "камень"):
        result = "Вы выиграли!"
        balances = load_json(BALANCE_FILE)
        balances[user_id] += 1.75
        save_json(BALANCE_FILE, balances)
    else:
        result = "Вы проиграли."
    bot.send_message(msg.chat.id, f"Бот выбрал: {bot_choice}\n{result}")
    game_states.pop(user_id)
@bot.message_handler(func=lambda msg: msg.text == "Моя статистика")
def handle_statistics(msg):
    user_id = str(msg.from_user.id)
    balances = load_json(BALANCE_FILE)
    referrals = load_json(REFERRALS_FILE)
    games_data = load_json(GAMES_FILE)
    investments = load_json(INVEST_FILE)
    levels = load_json(LEVELS_FILE)

    stats = games_data.get(user_id, {"games": 0, "wins": 0, "earnings": 0.0, "spend": 0.0, "ref_earn": 0.0})
    referrals_count = sum(1 for v in referrals.values() if v == user_id)
    referral_earn = round(referrals_count * 1.0 + stats.get("ref_earn", 0.0), 2)
    total_invest = sum(i['amount'] for i in investments.get(user_id, [])) if isinstance(investments.get(user_id, []), list) else 0
    net_profit = round(stats["earnings"] - stats["spend"], 2)

    total_earned = stats["earnings"] + referral_earn
    current_level = levels.get(user_id, "Новичок")

    level = "Новичок"
    reward = 0

    if total_earned >= 500:
        level, reward = "Профи", 50
    elif total_earned >= 150:
        level, reward = "Инвестор", 15
    elif total_earned >= 50:
        level, reward = "Игрок", 5

    if level != current_level:
        balances[user_id] = balances.get(user_id, 0) + reward
        levels[user_id] = level
        save_json(BALANCE_FILE, balances)
        save_json(LEVELS_FILE, levels)
        bot.send_message(msg.chat.id, f"Поздравляем! Новый уровень: {level} (+{reward} USDT)")

    bot.send_message(msg.chat.id, f"""
Ваша статистика:
Баланс: {balances.get(user_id, 0)} USDT
Сыграно игр: {stats['games']}
Побед: {stats['wins']}
Заработано: {stats['earnings']} USDT
Потрачено: {stats['spend']} USDT
Доход по рефералам: {referral_earn} USDT
Инвестировано: {total_invest} USDT
Чистая прибыль: {net_profit} USDT
Приглашено: {referrals_count}
Уровень: {level}
""")
@bot.message_handler(func=lambda msg: msg.text in ["Вложить 150$", "Вложить 300$", "Вложить 700$"])
def handle_investment(msg):
    user_id = str(msg.from_user.id)
    amount = int(msg.text.split()[1].replace("$", ""))
    plans = {150: 5, 300: 10, 700: 23}
    balances = load_json(BALANCE_FILE)
    investments = load_json(INVEST_FILE)

    if balances.get(user_id, 0) < amount:
        bot.send_message(msg.chat.id, "Недостаточно средств для инвестирования.")
        return

    balances[user_id] -= amount
    user_invests = investments.get(user_id, [])
    user_invests.append({
        "amount": amount,
        "daily": plans[amount],
        "start": time.time()
    })
    investments[user_id] = user_invests

    save_json(BALANCE_FILE, balances)
    save_json(INVEST_FILE, investments)

    bot.send_message(msg.chat.id, f"Вы успешно вложили {amount}$ и будете получать {plans[amount]}$ в день!")

# Фоновый поток для начисления прибыли
def investment_profit_loop():
    while True:
        investments = load_json(INVEST_FILE)
        balances = load_json(BALANCE_FILE)

        for user_id, invest_list in investments.items():
            total_profit = 0
            updated = []
            for invest in invest_list:
                last_pay = invest.get("last", invest["start"])
                if time.time() - last_pay >= 86400:
                    total_profit += invest["daily"]
                    invest["last"] = time.time()
                updated.append(invest)

            if total_profit > 0:
                balances[user_id] = balances.get(user_id, 0) + total_profit

            investments[user_id] = updated

        save_json(BALANCE_FILE, balances)
        save_json(INVEST_FILE, investments)
        time.sleep(60)

threading.Thread(target=investment_profit_loop, daemon=True).start()
@bot.message_handler(func=lambda msg: user_states.get(str(msg.from_user.id)) == "awaiting_withdraw")
def process_withdraw(msg):
    user_id = str(msg.from_user.id)
    try:
        amount_str, wallet = msg.text.strip().split()
        amount = float(amount_str)
        balances = load_json(BALANCE_FILE)

        if amount < 25:
            bot.send_message(msg.chat.id, "Минимальная сумма для вывода — 25 USDT.")
            return

        if balances.get(user_id, 0) < amount:
            bot.send_message(msg.chat.id, "Недостаточно средств.")
            return

        balances[user_id] -= amount
        save_json(BALANCE_FILE, balances)
        bot.send_message(msg.chat.id, f"Запрос на вывод {amount} USDT на адрес {wallet} принят.")
    except:
        bot.send_message(msg.chat.id, "Ошибка ввода. Формат: СУММА КОШЕЛЕК")

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    user_id = str(message.from_user.id)
    admins = load_json(ADMINS_FILE)

    if user_id in admins.get("main", []) or user_id in admins.get("subs", []):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Список пользователей", "Проверить баланс", "Изменить баланс")
        if user_id in admins.get("main", []):
            markup.add("Добавить субадмина", "Удалить субадмина")
        bot.send_message(message.chat.id, "Админ-панель:", reply_markup=markup)
        user_states[user_id] = "admin_menu"
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админке.")

@bot.message_handler(func=lambda msg: user_states.get(str(msg.from_user.id)) == "admin_menu")
def handle_admin_menu(msg):
    user_id = str(msg.from_user.id)
    text = msg.text.lower()
    if text == "список пользователей":
        balances = load_json(BALANCE_FILE)
        bot.send_message(msg.chat.id, f"Всего пользователей: {len(balances)}")
    elif text == "проверить баланс":
        bot.send_message(msg.chat.id, "Введите ID пользователя:")
        user_states[user_id] = "check_balance"
    elif text == "изменить баланс":
        bot.send_message(msg.chat.id, "Формат: ID СУММА (например: 123456 10 или 123456 -5)")
        user_states[user_id] = "change_balance"
    elif text == "добавить субадмина":
        bot.send_message(msg.chat.id, "Введите ID для добавления субадмина:")
        user_states[user_id] = "add_subadmin"
    elif text == "удалить субадмина":
        bot.send_message(msg.chat.id, "Введите ID для удаления субадмина:")
        user_states[user_id] = "remove_subadmin"

@bot.message_handler(func=lambda msg: user_states.get(str(msg.from_user.id)) in ["check_balance", "change_balance", "add_subadmin", "remove_subadmin"])
def handle_admin_actions(msg):
    user_id = str(msg.from_user.id)
    state = user_states[user_id]
    text = msg.text.strip()
    balances = load_json(BALANCE_FILE)
    admins = load_json(ADMINS_FILE)

    if state == "check_balance":
        if text in balances:
            bot.send_message(msg.chat.id, f"Баланс: {balances[text]} USDT")
        else:
            bot.send_message(msg.chat.id, "Пользователь не найден.")
    elif state == "change_balance":
        try:
            uid, amount = text.split()
            amount = float(amount)
            balances[uid] = balances.get(uid, 0) + amount
            save_json(BALANCE_FILE, balances)
            bot.send_message(msg.chat.id, f"Баланс обновлён: {balances[uid]} USDT")
        except:
            bot.send_message(msg.chat.id, "Ошибка формата.")
    elif state == "add_subadmin":
        if text not in admins["subs"]:
            admins["subs"].append(text)
            save_json(ADMINS_FILE, admins)
            bot.send_message(msg.chat.id, "Субадмин добавлен.")
        else:
            bot.send_message(msg.chat.id, "Уже субадмин.")
    elif state == "remove_subadmin":
        if text in admins["subs"]:
            admins["subs"].remove(text)
            save_json(ADMINS_FILE, admins)
            bot.send_message(msg.chat.id, "Субадмин удалён.")
        else:
            bot.send_message(msg.chat.id, "Не найден.")
    user_states[user_id] = "admin_menu"
@bot.message_handler(func=lambda msg: user_states.get(str(msg.from_user.id)) == "awaiting_deposit")
def process_deposit(msg):
    user_id = str(msg.from_user.id)
    try:
        amount = float(msg.text)
        if amount < 1:
            bot.send_message(msg.chat.id, "Минимум 1 USDT.")
            return

        deposit_link = f"https://pay.cryptocloud.plus/pos/JKgg8RePxKEsnTC0?amount={amount}"
        bot.send_message(msg.chat.id, f"Оплатите по ссылке:\n{deposit_link}\n\nПосле оплаты, свяжитесь с админом для подтверждения.")
        user_states.pop(user_id)
    except:
        bot.send_message(msg.chat.id, "Введите корректную сумму.")

# Запуск бота
print("Бот ТРК запущен...")
bot.polling(none_stop=True)
