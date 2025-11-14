import os
import logging
import time
import random
import sqlite3
from flask import Flask, request, abort
import telebot
from telebot import types

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables (set these in Render)
BOT_TOKEN = os.environ.get("TOKEN")
WEBHOOK_BASE = os.environ.get("WEBHOOK_URL")  # e.g. "https://your-service.onrender.com"
if not BOT_TOKEN:
    logger.error("TOKEN env var not set. Exiting.")
    raise SystemExit("TOKEN env var not set")
if not WEBHOOK_BASE:
    logger.error("WEBHOOK_URL env var not set. Exiting.")
    raise SystemExit("WEBHOOK_URL env var not set")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# --- DB setup (same as original) ---
DB_FILE = 'likes_requests.db'
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            uid TEXT,
            amount INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Mock API function (replace with real FF API)
def send_likes_to_ff(uid, amount):
    time.sleep(random.randint(2, 5))
    return {'success': True, 'new_likes': amount, 'message': f'Added {amount} likes to UID {uid}!'}

user_requests = {}

# Handlers (same logic as your original bot)
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/addlikes <UID> <amount> - e.g., /addlikes 123456789 50')
    markup.add(btn1)
    bot.send_message(
        message.chat.id,
        '🚀 Welcome to FF Likes Booster Bot!\n\n'
        '⚠️ WARNING: Use at your own risk - may violate ToS!\n\n'
        'Commands:\n/addlikes <Free Fire UID> <likes amount> (max 100/day)\n\n'
        'Example: /addlikes 123456789 50',
        reply_markup=markup
    )
    logger.info(f'User {message.from_user.id} started the bot.')

@bot.message_handler(commands=['addlikes'])
def add_likes(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, '❌ Invalid format! Use: /addlikes <UID> <amount>')
            return
        uid = parts[1]
        amount = int(parts[2])
        if amount > 100 or amount < 1:
            bot.send_message(message.chat.id, '❌ Max 100 likes per request! Keep it natural.')
            return
        now = time.time()
        if user_id in user_requests and (now - user_requests[user_id]) < 600:
            bot.send_message(message.chat.id, '⏳ Chill! Wait 10 mins between requests.')
            return
        user_requests[user_id] = now
        result = send_likes_to_ff(uid, amount)
        if result['success']:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO requests (user_id, uid, amount) VALUES (?, ?, ?)', (user_id, uid, amount))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, f'✅ {result["message"]}\n\n📊 Check your Free Fire profile in-game (refresh may take time).')
            logger.info(f'User {user_id} requested {amount} likes for UID {uid}.')
        else:
            bot.send_message(message.chat.id, '❌ Failed! Check UID and try again.')
    except ValueError:
        bot.send_message(message.chat.id, '❌ Amount must be a number!')
    except Exception:
        logger.exception("Error in add_likes")
        bot.send_message(message.chat.id, '❌ Something went wrong! Try later.')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, '👋 Use /start for commands!')

# Flask app + webhook endpoint
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'OK', 200

WEBHOOK_PATH = f"/{BOT_TOKEN}"
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

# configure webhook on start
def set_webhook():
    webhook_url = WEBHOOK_BASE.rstrip('/') + WEBHOOK_PATH
    logger.info(f"Setting webhook to: {webhook_url}")
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    if not success:
        logger.error("Failed to set webhook")
    else:
        logger.info("Webhook set successfully")

set_webhook()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
