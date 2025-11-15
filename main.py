import os
import logging
import asyncio
from flask import Flask, request, jsonify

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --------------------------------------
# CONFIG
# --------------------------------------
BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------
# TELEGRAM BOT
# --------------------------------------
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live!")

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /like <FF_ID>")

    ff_id = context.args[0]
    await update.message.reply_text("Processing...")

    import requests

    try:
        r = requests.get(f"{CLOUDFLARE_URL}/like?id={ff_id}")
        data = r.json()

        if data.get("status") == "success":
            await update.message.reply_text(f"Likes added: {data.get('likes',0)}")
        else:
            await update.message.reply_text("Failed!")
    except:
        await update.message.reply_text("Server error!")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

# --------------------------------------
# FLASK SERVER
# --------------------------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot running on webhook!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, application.bot)
    asyncio.create_task(application.process_update(update))
    return jsonify({"ok": True})

# --------------------------------------
# START TELEGRAM + FLASK
# --------------------------------------
async def run_bot():
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.start()

asyncio.get_event_loop().run_until_complete(run_bot())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    
