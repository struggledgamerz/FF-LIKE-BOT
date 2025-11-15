import logging
import asyncio
import os
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# -----------------------------
# CONFIG
# -----------------------------
BOT_TOKEN = "YOUR_BOT_TOKEN"
CLOUDFLARE_URL = "https://fails-earning-millions-informational.trycloudflare.com"
DOMAIN = "ff-like-bot-px1w.onrender.com"
WEBHOOK_URL = f"https://{DOMAIN}/webhook"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

# Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# SINGLE EVENT LOOP (Very Important)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


# -----------------------------
# BOT COMMANDS
# -----------------------------
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
    except:
        await update.message.reply_text("Server error!")


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("like", like))


# -----------------------------
# INIT BOT (Webhook)
# -----------------------------
async def init_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    print("Webhook set to:", WEBHOOK_URL)


# Run async init in our single loop
loop.run_until_complete(init_bot())


# -----------------------------
# WEBHOOK ROUTE
# -----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.json, application.bot)

    # Process update inside SAME event loop
    loop.create_task(application.process_update(update))

    return jsonify({"ok": True})


@app.route("/")
def home():
    return "Bot Running!"


# -----------------------------
# START SERVER
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    
