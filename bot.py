import os
import re

import gdown

from dotenv import load_dotenv

from whisper_service import transcribe
from gemini_service import find_best_clips
from video_editor import create_clip

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

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")


DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Welcome to ClipGenius AI\n\n"
        "Send me a Google Drive video link."
    )


async def handle_drive(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    if "drive.google.com" not in text:

        await update.message.reply_text(
            "❌ Please send a valid Google Drive link."
        )

        return


    status = await update.message.reply_text(
        "⬇️ Downloading video..."
    )


    try:

        # -------------------------
        # GET GOOGLE DRIVE FILE ID
        # -------------------------

        match = re.search(
            r"/d/([a-zA-Z0-9_-]+)",
            text
        )

        if not match:

            match = re.search(
                r"id=([a-zA-Z0-9_-]+)",
                text
            )


        if not match:

            await status.edit_text(
                "❌ Couldn't find Google Drive File ID."
            )

            return


        file_id = match.group(1)


        url = (
            f"https://drive.google.com/uc"
            f"?id={file_id}"
        )


        video_path = os.path.join(
            DOWNLOAD_FOLDER,
            f"{file_id}.mp4"
        )


        # -------------------------
        # DOWNLOAD
        # -------------------------

        gdown.download(
            url,
            video_path,
            quiet=False
        )


        if not os.path.exists(video_path):

            raise RuntimeError(
                "Video download failed."
            )


        await status.edit_text(
            "✅ Download complete!\n\n"
            "📝 Starting Whisper transcription..."
        )


        print("Starting Whisper...")


        # -------------------------
        # WHISPER
        # -------------------------

        segments = transcribe(video_path)


        if not segments:

            raise RuntimeError(
                "Whisper found no speech."
            )


        print(
            f"Whisper found {len(segments)} segments."
        )


        # Create readable transcript

        transcript_file = os.path.join(
            DOWNLOAD_FOLDER,
            "transcript.txt"
        )


        with open(
            transcript_file,
            "w",
            encoding="utf-8"
        ) as f:

            for segment in segments:

                f.write(
                    f"[{segment['start']:.2f} - "
                    f"{segment['end']:.2f}] "
                    f"{segment['text']}\n"
                )


        await update.message.reply_document(
            document=open(
                transcript_file,
                "rb"
            ),
            caption="✅ Transcription completed!"
        )


        # -------------------------
        # GEMINI
        # -------------------------

        await status.edit_text(
            "🤖 Gemini is finding the strongest viral moments..."
        )


        print("Sending transcript to Gemini...")


        clips = find_best_clips(
            segments,
            max_clips=5
        )


        if not clips:

            raise RuntimeError(
                "Gemini did not find any clips."
            )


        print(
            f"Gemini selected {len(clips)} clips."
        )


        # -------------------------
        # CREATE CLIPS
        # -------------------------

        await status.edit_text(
            f"✂️ Creating {len(clips)} viral clips..."
        )


        for index, clip in enumerate(
            clips,
            start=1
        ):

            print(
                f"Creating clip {index}: "
                f"{clip['start']} - {clip['end']}"
            )


            clip_path = create_clip(
                video_path,
                clip["start"],
                clip["end"],
                index
            )


            caption = (
                f"🔥 Viral Clip {index}\n\n"
                f"🎯 {clip['hook']}\n\n"
                f"💡 {clip['reason']}\n\n"
                f"⏱️ "
                f"{clip['start']:.1f}s → "
                f"{clip['end']:.1f}s"
            )


            await update.message.reply_video(
                video=open(
                    clip_path,
                    "rb"
                ),
                caption=caption
            )


        await status.edit_text(
            f"✅ Done!\n\n"
            f"🔥 Created {len(clips)} viral clips."
        )


    except Exception as e:

        print("ERROR:", repr(e))

        await status.edit_text(
            f"❌ Error:\n{e}"
        )


def main():

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


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
