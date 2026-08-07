import os
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
        "👋 Welcome!\n\n"
        "Send me a video and I'll download it for processing."
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document

    if not video:
        await update.message.reply_text("❌ Please send a video.")
        return

    status = await update.message.reply_text("📥 Receiving your video...")

    try:
        file = await context.bot.get_file(video.file_id)

        filename = f"{video.file_unique_id}.mp4"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        await status.edit_text("⬇️ Downloading video...")

        await file.download_to_drive(custom_path=filepath)

        size_mb = round(video.file_size / (1024 * 1024), 2)

        await status.edit_text(
            f"✅ Download complete!\n\n"
            f"📁 File: {filename}\n"
            f"📦 Size: {size_mb} MB\n\n"
            f"Next step: AI processing..."
        )

    except Exception as e:
        print(e)
        await status.edit_text(f"❌ Error:\n{e}")


def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .read_timeout(600)
        .write_timeout(600)
        .connect_timeout(60)
        .pool_timeout(60)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
