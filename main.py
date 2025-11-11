import telebot
import requests
import sqlite3
import time
import random
import logging
from telebot import types

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Replace with your Bot Token from BotFather
BOT_TOKEN = '7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8'
bot = telebot.TeleBot(BOT_TOKEN)

# Database setup (SQLite for storing requests - optional)
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

# Mock API function (replace with real Free Fire API call)
def send_likes_to_ff(uid, amount):
    """
    Simulates sending likes to Free Fire UID.
    In reality: Use requests.post to an API like RapidAPI's FF endpoint with JWT auth.
    Example real call (uncomment and configure):
    # url = 'https://free-fire-api.p.rapidapi.com/likes/add'
    # headers = {'X-RapidAPI-Key': 'YOUR_API_KEY'}
    # data = {'uid': uid, 'amount': amount}
    # response = requests.post(url, headers=headers, json=data)
    # return response.json() if response.ok else None
    """
    # Mock response - in real bot, this would increment likes
    time.sleep(random.randint(2, 5))  # Simulate delay
    return {'success': True, 'new_likes': amount, 'message': f'Added {amount} likes to UID {uid}!'}

# Rate limiting: Simple dict to track user requests (in production, use Redis)
user_requests = {}  # {user_id: last_request_time}

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
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
    logger.info(f'User {user_id} started the bot.')

@bot.message_handler(commands=['addlikes'])
def add_likes(message):
    user_id = message.from_user.id
    try:
        # Parse command: /addlikes <uid> <amount>
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, '❌ Invalid format! Use: /addlikes <UID> <amount>')
            return
        
        uid = parts[1]
        amount = int(parts[2])
        
        if amount > 100 or amount < 1:
            bot.send_message(message.chat.id, '❌ Max 100 likes per request! Keep it natural.')
            return
        
        # Simple rate limit: 1 request per 10 mins per user
        now = time.time()
        if user_id in user_requests and (now - user_requests[user_id]) < 600:
            bot.send_message(message.chat.id, '⏳ Chill! Wait 10 mins between requests.')
            return
        user_requests[user_id] = now
        
        # Send to FF (mock)
        result = send_likes_to_ff(uid, amount)
        
        if result['success']:
            # Log to DB
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO requests (user_id, uid, amount) VALUES (?, ?, ?)', (user_id, uid, amount))
            conn.commit()
            conn.close()
            
            bot.send_message(
                message.chat.id,
                f'✅ {result["message"]}\n\n'
                f'📊 Check your Free Fire profile in-game (refresh may take time).\n'
                f'💡 Tip: Play Craftland for organic likes!'
            )
            logger.info(f'User {user_id} requested {amount} likes for UID {uid}.')
        else:
            bot.send_message(message.chat.id, '❌ Failed! Check UID and try again.')
    
    except ValueError:
        bot.send_message(message.chat.id, '❌ Amount must be a number!')
    except Exception as e:
        logger.error(f'Error in add_likes: {e}')
        bot.send_message(message.chat.id, '❌ Something went wrong! Try later.')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, '👋 Use /start for commands!')

if __name__ == '__main__':
    logger.info('Bot starting...')
    bot.infinity_polling()
