import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request, jsonify
import requests
import asyncio
import os

# -------------------------------
# CONFIG
# -------------------------------
BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# TELEGRAM BOT
# -------------------------------
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like <FF_ID>")
        return

    ff_id = context.args[0]

    await update.message.reply_text("Processing...")

    try:
        res = requests.get(f"{CLOUDFLARE_URL}/like?id={ff_id}", timeout=20)
        data = res.json()

        if data.get("status") == "success":
            await update.message.reply_text(f"Likes added: {data.get('likes', 0)}")
        else:
            await update.message.reply_text("Failed to add likes")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Server error!")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

# -------------------------------
# FLASK APP
# -------------------------------
app = Flask(__name__)


# Run Telegram initialization only once
bot_started = False

@app.before_request
def start_bot_once():
    global bot_started
    if not bot_started:
        loop = asyncio.get_event_loop()
        loop.create_task(init_bot())
        bot_started = True


async def init_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    print("WEBHOOK SET:", WEBHOOK_URL)


@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, application.bot)
    loop = asyncio.get_event_loop()
    loop.create_task(application.process_update(update))
    return jsonify({"ok": True})


@app.route("/")
def home():
    return "Bot Running via Render"


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    
