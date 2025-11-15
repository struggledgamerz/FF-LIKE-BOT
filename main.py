import logging
import threading
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os

# -------------------
# CONFIG
# -------------------
BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"
DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------
# TELEGRAM APP
# -------------------
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
        r = requests.get(f"{CLOUDFLARE_URL}/like?id={ff_id}")
        data = r.json()

        if data.get("status") == "success":
            await update.message.reply_text(f"Likes added: {data.get('likes')}")
        else:
            await update.message.reply_text("Failed to add likes.")
    except Exception as e:
        await update.message.reply_text("Server error!")
        print("ERROR:", e)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))


# -------------------
# RUN TELEGRAM BOT LOOP IN BACKGROUND
# -------------------
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    loop.run_until_complete(application.bot.set_webhook(WEBHOOK_URL))
    loop.run_forever()

threading.Thread(target=run_bot, daemon=True).start()


# -------------------
# FLASK SERVER
# -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, application.bot)
    asyncio.run(application.process_update(update))
    return jsonify({"ok": True})


# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
        
