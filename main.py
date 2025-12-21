from flask import Flask
import threading
import telebot
import os

# --------- Web Server برای آنلاین نگه داشتن ربات ---------
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# --------- ربات تلگرام ---------
TOKEN = os.environ['TOKEN']  # توکن از Environment Variable خوانده می‌شود
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! من ربات تو هستم!")

# فعال کردن Web Server
keep_alive()

# شروع ربات
bot.polling(none_stop=True)
