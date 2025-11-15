import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request, jsonify
import requests
import asyncio
import os

# -------------------------------------
# CONFIG
# -------------------------------------

BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"

DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------
# TELEGRAM BOT HANDLERS
# -------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Running ✔")

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like <FF_ID>")
        return

    ff_id = context.args[0]
    await update.message.reply_text("Processing...")

    try:
        res = requests.get(f"{CLOUDFLARE_URL}/like?id={ff_id}")
        data = res.json()

        if data.get("status") == "success":
            await update.message.reply_text(f"❤️ Likes added: {data.get('likes', 0)}")
        else:
            await update.message.reply_text("Failed to add likes ❌")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Server Error! ❌")

# -------------------------------------
# FLASK + TELEGRAM APPLICATION
# -------------------------------------

app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

# Telegram init (NOT inside webhook)
async def init_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    print("Webhook set:", WEBHOOK_URL)

# Run async init once
asyncio.get_event_loop().create_task(init_bot())

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, application.bot)

    # QUEUE UPDATE instead of running new loop
    asyncio.get_event_loop().create_task(application.process_update(update))

    return jsonify({"ok": True})

@app.route("/")
def home():
    return "Bot Running ✔"

# -------------------------------------
# RUN SERVER
# -------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    
