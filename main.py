import logging
import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
DOMAIN = "https://ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------
# TELEGRAM HANDLERS
# ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is live on webhook!")

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Like function working!")

# ----------------------
# FLASK APP
# ----------------------
app = Flask(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

# ----------------------
# INITIALIZE TELEGRAM APP
# ----------------------
async def init_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    print("Webhook set:", WEBHOOK_URL)

loop.run_until_complete(init_bot())

# ----------------------
# FLASK ROUTES
# ----------------------
@app.route("/webhook", methods=["POST"])
def receive_update():
    update = Update.de_json(request.json, application.bot)
    loop.create_task(application.process_update(update))
    return jsonify({"ok": True})

@app.route("/")
def home():
    return "Bot Running on Render"

# ----------------------
# START SERVER
# ----------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    
