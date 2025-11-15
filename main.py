import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread
import requests
import os
import asyncio

BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Telegram Bot Handlers
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")

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
            await update.message.reply_text(f"Likes added: {data.get('likes', 0)}")
        else:
            await update.message.reply_text("Failed to add likes")

    except Exception as e:
        print(e)
        await update.message.reply_text("Server error!")

# ---------------------------
# Telegram Bot (Polling)
# ---------------------------

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

def run_bot():
    asyncio.run(application.run_polling())

# ---------------------------
# Flask Server (Render ke liye)
# ---------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running on Render using polling!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------------------------
# Run both in two threads
# ---------------------------

if __name__ == "__main__":
    Thread(target=run_bot).start()
    Thread(target=run_flask).start()
    
