from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Send me a video and I'll create viral clips from it."
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ Video received.\n\nProcessing... Please wait."
    )

    video = await update.message.video.get_file()
    await video.download_to_drive("input.mp4")

    # AI clipping code will be added here later.

    await update.message.reply_text(
        "✅ Video uploaded successfully."
    )

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))

app.run_polling()
