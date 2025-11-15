import logging
import os
import asyncio
import requests
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# -------------------------
# CONFIG
# -------------------------
BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"

DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# FLASK APP
# -------------------------
app = Flask(__name__)

# Global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Create Telegram Application (async)
application = Application.builder().token(BOT_TOKEN).build()

# -------------------------
# TELEGRAM COMMANDS
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like <FF_ID>")
        return

    ff_id = context.args[0]
    await update.message.reply_text("Processing...")

    try:
        r = requests.get(f"{CLOUDFLARE_URL}/like?id={ff_id}", timeout=15)
        data = r.json()

        if data.get("status") == "success":
            await update.message.reply_text(f"Likes Added: {data.get('likes')}")
        else:
            await update.message.reply_text("Failed to add likes")
    except Exception as e:
        await update.message.reply_text("Server Error!")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

# -------------------------
# INITIALIZE BOT (ONE TIME)
# -------------------------
async def init_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    print("Webhook set to:", WEBHOOK_URL)

loop.create_task(init_bot())

# -------------------------
# FLASK ROUTES
# -------------------------
@app.route("/", methods=["GET"])
def home():
    return "Bot Running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, application.bot)

    # Process telegram update inside async loop safely
    loop.create_task(application.process_update(update))

    return jsonify({"ok": True})

# -------------------------
# RUN SERVER
# -------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
        
