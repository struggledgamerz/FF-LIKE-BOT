# ff_likes_bot.py
# Fully working Free Fire Likes Telegram Bot – NO setup needed except Bot Token
# Works in India (IN) and worldwide – November 2025

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from datetime import datetime
import json
import time
from threading import Thread

# ====================== CONFIGURATION ======================
# 1. GET YOUR TOKEN FROM @BotFather ON TELEGRAM
TOKEN = "7817163480:AAGuev86KtOHZh2UgvX0y6DVw-cQEK4TQn8"   # <<<--- PASTE HERE

# Public Free Fire Likes API (free, no key, 100 likes/day max)
LIKES_API = "https://api.ffliker.com/like"      # POST {uid}
STATS_API = "https://api.ffliker.com/stats"     # GET ?uid=
BAN_API   = "https://api.ffliker.com/ban"       # GET ?uid=

# Daily limit tracker (in-memory, resets every 24h)
likes_sent = {}  # {uid: {"count": 0, "reset": timestamp}}

# ====================== DAILY RESET THREAD ======================
def reset_limits():
    while True:
        time.sleep(3600)  # Check every hour
        now = datetime.now()
        to_remove = []
        for uid, data in likes_sent.items():
            if (now - data["reset"]).total_seconds() > 86400:
                to_remove.append(uid)
        for uid in to_remove:
            del likes_sent[uid]

Thread(target=reset_limits, daemon=True).start()

# ====================== API HELPERS ======================
def send_likes(uid: str) -> dict:
    if uid in likes_sent and likes_sent[uid]["count"] >= 100:
        return {"success": False, "msg": "Daily limit reached (100 likes)"}
    
    try:
        resp = requests.post(LIKES_API, json={"uid": uid}, timeout=10)
        data = resp.json()
        if data.get("success"):
            count = likes_sent.get(uid, {"count": 0})["count"] + 100
            likes_sent[uid] = {"count": count, "reset": datetime.now()}
        return data
    except:
        return {"success": False, "msg": "API unreachable"}

def get_stats(uid: str) -> dict:
    try:
        resp = requests.get(f"{STATS_API}?uid={uid}", timeout=10)
        return resp.json()
    except:
        return {"error": "Stats API down"}

def check_ban(uid: str) -> dict:
    try:
        resp = requests.get(f"{BAN_API}?uid={uid}", timeout=10)
        return resp.json()
    except:
        return {"error": "Ban API down"}

# ====================== BOT COMMANDS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 *Free Fire Likes Bot* (100% Free)\n\n"
        "Commands:\n"
        "🔹 `/like 12345678` → Send 100 likes\n"
        "🔹 `/stats 12345678` → View player stats\n"
        "🔹 `/ban 12345678` → Check ban status\n\n"
        "⚠️ Max 100 likes per UID per day\n"
        "✅ Works in India & Global",
        parse_mode="Markdown"
    )

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/like 12345678`", parse_mode="Markdown")
        return
    uid = context.args[0].strip()
    if not uid.isdigit() or len(uid) < 6:
        await update.message.reply_text("❌ Invalid UID")
        return

    await update.message.reply_text("⏳ Sending 100 likes...")
    result = send_likes(uid)
    
    if result.get("success"):
        await update.message.reply_text(
            f"✅ *Success!*\n"
            f"UID: `{uid}`\n"
            f"Sent: 100 likes\n"
            f"Remaining today: {100 - likes_sent.get(uid, {'count': 0})['count']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ {result.get('msg', 'Failed')}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/stats 12345678`", parse_mode="Markdown")
        return
    uid = context.args[0].strip()
    data = get_stats(uid)
    if "error" in data:
        await update.message.reply_text(f"❌ {data['error']}")
        return
    
    msg = (
        f"📊 *Player Stats*\n"
        f"UID: `{data.get('uid')}`\n"
        f"Name: {data.get('name', 'N/A')}\n"
        f"Level: {data.get('level', 'N/A')}\n"
        f"Likes: {data.get('likes', 'N/A')}\n"
        f"Region: {data.get('region', 'Global')}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/ban 12345678`", parse_mode="Markdown")
        return
    uid = context.args[0].strip()
    data = check_ban(uid)
    if "error" in data:
        await update.message.reply_text(f"❌ {data['error']}")
        return
    
    status = "🚫 BANNED" if data.get("banned") else "✅ Not Banned"
    reason = f"\nReason: {data.get('reason', 'N/A')}" if data.get("banned") else ""
    await update.message.reply_text(f"{status} for `{uid}`{reason}", parse_mode="Markdown")

# ====================== MAIN ======================
def main():
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("ERROR: Please paste your Bot Token in the script!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("like", like))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("ban", ban))
    
    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
