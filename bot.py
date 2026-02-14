import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_ID_RAW = os.getenv("ALLOWED_TELEGRAM_USER_ID", "").strip()

DATA_DIR = Path("data")
VOICE_DIR = DATA_DIR / "voice"
VOICE_DIR.mkdir(parents=True, exist_ok=True)

def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)

def allowed_user_id() -> int | None:
    if not ALLOWED_USER_ID_RAW:
        return None
    try:
        return int(ALLOWED_USER_ID_RAW)
    except ValueError:
        return None

def is_allowed(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else None
    allow = allowed_user_id()
    return (allow is not None) and (uid == allow)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id if update.effective_user else None
    uname = update.effective_user.username if update.effective_user else None
    log(f"/start from user_id={uid} username={uname}")

    if not is_allowed(update):
        # HARD RULE: Do not communicate with unknown users.
        # We only log the user_id so Roman can whitelist himself.
        return

    await update.message.reply_text("✅ Bot ist online. Text & Voice sind aktiv.")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id if update.effective_user else None
    log(f"/help from user_id={uid}")

    if not is_allowed(update):
        return

    await update.message.reply_text("Befehle: /start, /help\nSende Text oder eine Voice-Message.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id if update.effective_user else None
    text = update.message.text if update.message else ""
    log(f"text from user_id={uid}: {text[:120]!r}")

    if not is_allowed(update):
        return

    await update.message.reply_text("✅ Text empfangen.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id if update.effective_user else None
    voice = update.message.voice if update.message else None
    log(f"voice from user_id={uid}: present={voice is not None}")

    if not voice:
        return

    # Always download only if allowed (hard rule).
    if not is_allowed(update):
        return

    file = await context.bot.get_file(voice.file_id)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = VOICE_DIR / f"{ts}_{voice.file_id}.ogg"
    await file.download_to_drive(custom_path=str(out_path))

    await update.message.reply_text(f"✅ Voice gespeichert: {out_path}")

def main() -> None:
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN fehlt in .env", file=sys.stderr)
        sys.exit(1)

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    log("Bot startet (Polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
