import os
import re
import gdown

from dotenv import load_dotenv
from whisper_service import transcribe
from gemini_service import find_best_clips

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

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
        await update.message.reply_text(
            "❌ Please send a valid Google Drive link."
        )
        return

    status = await update.message.reply_text(
        "⬇️ Downloading from Google Drive..."
    )

    try:
        # Extract Google Drive File ID
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", text)

        if not match:
            match = re.search(r"id=([a-zA-Z0-9_-]+)", text)

        if not match:
            await status.edit_text("❌ Couldn't find Google Drive File ID.")
            return

        file_id = match.group(1)

        url = f"https://drive.google.com/uc?id={file_id}"

        output = os.path.join(
            DOWNLOAD_FOLDER,
            f"{file_id}.mp4"
        )

        # Download video
        gdown.download(url, output, quiet=False)

        await status.edit_text(
            "✅ Download complete!\n\n"
            "📝 Starting Whisper transcription..."
        )

        print("Starting Whisper...")

        # Whisper transcription
        transcript = transcribe(output)

        transcript_file = "transcript.txt"

        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcript)

        await update.message.reply_document(
            document=open(transcript_file, "rb"),
            caption="✅ Transcription completed!"
        )

        # Gemini Analysis
        await status.edit_text(
            "🤖 Gemini is finding the best viral clips..."
        )

        clips = find_best_clips(transcript)

        await update.message.reply_text(
            "🔥 Best Viral Clips\n\n" + clips
        )

    except Exception as e:
        await status.edit_text(f"❌ Error:\n{e}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_drive
        )
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
