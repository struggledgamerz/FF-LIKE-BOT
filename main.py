import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import requests
import os

# Telegram Bot Token
BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"

# Cloudflare tunnel URL
CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"

# Render domain
DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------
# TELEGRAM COMMANDS
# ---------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is Online ✅")

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like <FF_ID>")
        return
    
    ff_id = context.args[0]
    await update.message.reply_text("Processing...⏳")

    try:
        r = requests.get(f"{CLOUDFLARE_URL}/like?id={ff_id}", timeout=15)
        data = r.json()

        if data.get("status") == "success":
            await update.message.reply_text(f"❤️ Likes added: {data.get('likes',0)}")
        else:
            await update.message.reply_text("❌ Failed to add likes")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Server error")


# ---------------------------------------
# FLASK APP
# ---------------------------------------

app = Flask(__name__)

# Telegram Application (async bot)
application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

# Create Global Event Loop
loop = asyncio.get_event_loop()

# Set Webhook Once App Starts
@app.before_first_request
def setup_webhook():
    loop.create_task(application.bot.set_webhook(WEBHOOK_URL))
    loop.create_task(application.initialize())
    loop.create_task(application.start())
    print("Webhook Set:", WEBHOOK_URL)

# Webhook Receiver Route
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, application.bot)
    loop.create_task(application.process_update(update))
    return jsonify({"ok": True})

@app.route("/")
def home():
    return "Bot Running on Render ✔️"


# Run Flask normally (Render detects port)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    
