import os
import re
import gdown
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ClipGenius AI\n\n"
        "Send me a Google Drive video link."
    )


async def handle_drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "drive.google.com" not in text:
        await update.message.reply_text("❌ Please send a valid Google Drive link.")
        return

    status = await update.message.reply_text("⬇️ Downloading from Google Drive...")

    try:
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", text)

        if not match:
            match = re.search(r"id=([a-zA-Z0-9_-]+)", text)

        if not match:
            await status.edit_text("❌ Couldn't find file ID.")
            return

        file_id = match.group(1)

        url = f"https://drive.google.com/uc?id={file_id}"

        output = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp4")

        gdown.download(url, output, quiet=False)

        await status.edit_text(
            "✅ Download complete!\n\n"
            f"Saved to:\n{output}"
        )

    except Exception as e:
        await status.edit_text(f"❌ Error:\n{e}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_drive))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
