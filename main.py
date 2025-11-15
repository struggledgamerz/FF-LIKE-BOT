import logging
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import threading
import requests
import os

# -------------------------------
# CONFIG
# -------------------------------
BOT_TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"
CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"
DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------------
# TELEGRAM COMMANDS
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is online!")


async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /like <FF_ID>")
        return

    ff_id = context.args[0]

    await update.message.reply_text("⏳ Processing...")

    try:
        res = requests.get(f"{CLOUDFLARE_URL}/like?id={ff_id}", timeout=20)
        data = res.json()

        if data.get("status") == "success":
            await update.message.reply_text(f"❤️ Likes added: {data.get('likes',0)}")
        else:
            await update.message.reply_text("❌ Failed to add likes!")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Server error!")


# -------------------------------
# FLASK APP
# -------------------------------
app = Flask(__name__)

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))

# BACKGROUND EVENT LOOP
bot_loop = asyncio.new_event_loop()


def start_bot():
    asyncio.set_event_loop(bot_loop)
    bot_loop.create_task(application.initialize())
    bot_loop.create_task(application.start())
    bot_loop.create_task(application.bot.set_webhook(WEBHOOK_URL))
    bot_loop.run_forever()


threading.Thread(target=start_bot, daemon=True).start()


# -------------------------------
# WEBHOOK ENDPOINT
# -------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.json, application.bot)
        asyncio.run_coroutine_threadsafe(application.process_update(update), bot_loop)
    except Exception as e:
        logger.error(e)
        return jsonify({"ok": False})
    return jsonify({"ok": True})


@app.route("/")
def home():
    return "Bot Running on Render!"


# -------------------------------
# START FLASK SERVER
# -------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    
