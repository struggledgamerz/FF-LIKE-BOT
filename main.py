import os
import json
import logging
import requests
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import nest_asyncio

nest_asyncio.apply()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Set TOKEN in Render Environment Variables!")

DOMAIN = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if not DOMAIN:
    raise ValueError("RENDER_EXTERNAL_HOSTNAME not set!")

WEBHOOK_URL = f"https://{DOMAIN}/webhook"
BOT = Bot(TOKEN)

# Load guests
GUESTS = []
USED = set()

def load_guests():
    global GUESTS
    try:
        with open("guests/ff_guests.json", "r") as f:
            GUESTS = [json.loads(line.strip()) for line in f if line.strip()]
        logger.info(f"Loaded {len(GUESTS)} guests")
    except FileNotFoundError:
        logger.error("guests/ff_guests.json NOT FOUND! Upload to GitHub → guests/ff_guests.json")
    except Exception as e:
        logger.error(f"Load error: {e}")

load_guests()

# Daily like tracker
likes_sent = {}

def reset_daily():
    import time
    while True:
        time.sleep(3600)
        now = datetime.now()
        to_remove = [uid for uid, data in likes_sent.items() if (now - data["reset"]).total_seconds() > 86400]
        for uid in to_remove:
            del likes_sent[uid]
        logger.info("Daily like reset complete")

Thread(target=reset_daily, daemon=True).start()

# Free FF Stats API
STATS_API = "https://free-ff-api-src-5plp.onrender.com/api/v1/playerstats"

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "FREE FIRE BOT LIVE!\n\n"
        f"Guests: {len(GUESTS)}\n"
        f"Used: {len(USED)}\n\n"
        "Commands:\n"
        "/like 12345678 → 100 likes\n"
        "/stats 12345678 → Real stats\n"
        "/ban 12345678 → Ban check\n\n"
        "India & Global | 100 likes/day"
    )

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like 12345678")
        return
    uid = context.args[0].strip()
    if not uid.isdigit() or len(uid) < 8:
        await update.message.reply_text("Invalid UID!")
        return

    # Daily limit check
    today = likes_sent.get(uid, {"count": 0})["count"]
    if today >= 100:
        await update.message.reply_text("Daily limit reached! Try tomorrow.")
        return

    available = [g for g in GUESTS if g["jwt"] not in USED][:100]
    if not available:
        await update.message.reply_text("No fresh guests! Regenerate.")
        return

    await update.message.reply_text(f"Sending {len(available)} likes to {uid}...")

    sent = 0
    for guest in available:
        try:
            headers = {
                "Authorization": f"Bearer {guest['jwt']}",
                "Content-Type": "application/json",
                "User-Agent": "GarenaFreeFire/1.0"
            }
            payload = {
                "target_uid": int(uid),
                "count": 1,
                "region": guest.get("region", "IND")
            }
            response = requests.post(
                "https://ssg32-account.garena.com/like",
                json=payload,
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                sent += 1
                USED.add(guest["jwt"])
            await asyncio.sleep(0.3)  # Rate limit
        except Exception as e:
            logger.error(f"Like failed: {e}")

    # Update daily count
    likes_sent[uid] = {
        "count": today + sent,
        "reset": datetime.now()
    }

    await update.message.reply_text(
        f"REAL LIKES SENT: {sent}\n"
        f"Failed: {len(available) - sent}\n"
        f"Check in-game in 5-10 mins!"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /stats 12345678")
        return
    uid = context.args[0].strip()
    try:
        resp = requests.get(STATS_API, params={"region": "IND", "uid": uid}, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("basicInfo", {})
            msg = (
                f"*Real Player Stats*\n\n"
                f"Name: `{data.get('nickname', 'N/A')}`\n"
                f"Level: `{data.get('level', 'N/A')}`\n"
                f"Likes: `{data.get('liked', 'N/A')}`\n"
                f"Rank: `{data.get('rank', 'N/A')}`\n"
                f"Region: `IND`"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("Player not found or API down.")
    except:
        await update.message.reply_text("Stats temporarily unavailable.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /ban 12345678")
        return
    await update.message.reply_text("Ban check not available in free mode.\nUse /stats for player info.")

# Application
application = Application.builder().token(TOKEN).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("ban", ban))

# Flask app
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), BOT)
    await application.process_update(update)
    return jsonify(success=True)

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    try:
        BOT.set_webhook(url=WEBHOOK_URL)
        return f"Webhook set: {WEBHOOK_URL}"
    except Exception as e:
        return f"Error: {e}"

@app.route('/', methods=['GET'])
def home():
    return "Bot is LIVE! Send /start in Telegram."

# Run
if __name__ == "__main__":
    # Set webhook on startup
    Thread(target=lambda: BOT.set_webhook(url=WEBHOOK_URL), daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
