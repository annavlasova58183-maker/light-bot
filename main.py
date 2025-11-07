import telebot
from telebot import types
import os

# === Дані бота ===
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ Помилка: TELEGRAM_BOT_TOKEN не встановлений!")
    exit(1)

MANAGER_GROUP_ID = -1003164165301

bot = telebot.TeleBot(BOT_TOKEN)

# Сховище тимчасових даних операторів
user_reports = {}
user_last_report_msg = {}  # зберігає ID повідомлення звіту в групі керівників

# === Кнопки меню ===
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("⚡️ Заповнити звіт", "💡 Повернувся в лінію")
    return keyboard

# === Обробка старту ===
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Привіт! 👋\nОбери дію нижче:",
        reply_markup=main_menu()
    )

# === Обробка натискань кнопок ===
@bot.message_handler(func=lambda message: message.text == "⚡️ Заповнити звіт")
def start_report(message):
    user_reports[message.chat.id] = {}
    bot.send_message(message.chat.id, "Вкажіть ваше ПІБ:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_reports[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "До котрої години зможете працювати з телефона чи запасного живлення?")
    bot.register_next_step_handler(message, get_work_time)

def get_work_time(message):
    user_reports[message.chat.id]["work_time"] = message.text
    bot.send_message(message.chat.id, "Коли обіцяють подати світло?")
    bot.register_next_step_handler(message, get_light_return)

def get_light_return(message):
    user_reports[message.chat.id]["light_return"] = message.text
    bot.send_message(message.chat.id, "Надішліть фото чи скріншот як доказ 💡 (або напишіть 'пропустити'):")
    bot.register_next_step_handler(message, get_proof)

def get_proof(message):
    user_data = user_reports.get(message.chat.id, {})
    proof = None

    if message.photo:
        proof = message.photo[-1].file_id
    elif message.text.lower() != "пропустити":
        proof = message.text

    text = (
        f"⚡️ <b>Новий звіт — Без світла</b>\n\n"
        f"👤 ПІБ: {user_data.get('name')}\n"
        f"📱 Працює до: {user_data.get('work_time')}\n"
        f"💡 Світло обіцяють дати: {user_data.get('light_return')}"
    )

    # Відправляємо керівникам
    sent_msg = bot.send_message(MANAGER_GROUP_ID, text, parse_mode="HTML")
    user_last_report_msg[message.chat.id] = sent_msg.message_id  # зберігаємо ID цього повідомлення

    if proof and isinstance(proof, str) and not proof.startswith("AgAC"):
        bot.send_message(MANAGER_GROUP_ID, f"📎 Доказ: {proof}")
    elif proof:
        bot.send_photo(MANAGER_GROUP_ID, proof)

    bot.send_message(message.chat.id, "✅ Звіт відправлено керівникам!", reply_markup=main_menu())

# === Повідомлення про повернення ===
@bot.message_handler(func=lambda message: message.text == "💡 Повернувся в лінію")
def back_online(message):
    name = user_reports.get(message.chat.id, {}).get("name", message.from_user.first_name)
    reply_to_id = user_last_report_msg.get(message.chat.id)

    text = f"💡 <b>{name}</b> повернувся в лінію!"

    if reply_to_id:
        bot.send_message(MANAGER_GROUP_ID, text, parse_mode="HTML", reply_to_message_id=reply_to_id)
    else:
        bot.send_message(MANAGER_GROUP_ID, text, parse_mode="HTML")

    bot.send_message(message.chat.id, "Дякую! Передано керівникам ✅", reply_markup=main_menu())

# === Ігнор повідомлень із групи керівників ===
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def ignore_manager_group(message):
    if message.chat.id == MANAGER_GROUP_ID:
        return
    else:
        bot.send_message(message.chat.id, "Оберіть дію з меню 👇", reply_markup=main_menu())

# === Запуск ===
bot.polling(none_stop=True)