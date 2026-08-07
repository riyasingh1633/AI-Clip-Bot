import os
from telegram import Update
from telegram.ext import (
    Application,
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
        "👋 Welcome!\n\n"
        "Send me a video and I'll download it for processing."
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 Downloading your video...")

    video = update.message.video or update.message.document

    if not video:
        await update.message.reply_text("❌ Please send a video.")
        return

    file = await context.bot.get_file(video.file_id)

    filename = f"{video.file_unique_id}.mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    await file.download_to_drive(filepath)

    await update.message.reply_text(
        f"✅ Video downloaded!\nSaved as:\n{filename}\n\nNext we'll process it with AI."
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
