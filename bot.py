import os
import re
import asyncio
import gdown

from dotenv import load_dotenv

from whisper_service import transcribe
from gemini_service import find_best_clips
from video_editor import create_clip

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")


DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# --------------------------------------------------
# DEFAULT USER SETTINGS
# --------------------------------------------------

DEFAULT_SETTINGS = {
    "duration": 30,
    "clips": 5,
    "format": "original",
    "captions": True,
    "style": "viral",
}


def get_settings(context):
    if "settings" not in context.user_data:
        context.user_data["settings"] = DEFAULT_SETTINGS.copy()

    return context.user_data["settings"]


# --------------------------------------------------
# SETTINGS MENU
# --------------------------------------------------

def settings_keyboard(settings):

    duration = settings["duration"]

    if duration == 0:
        duration_text = "Custom"
    else:
        duration_text = f"{duration}s"

    format_text = {
        "original": "Original",
        "9:16": "9:16",
        "1:1": "1:1",
        "16:9": "16:9",
    }.get(settings["format"], settings["format"])

    captions_text = "ON" if settings["captions"] else "OFF"

    style_text = {
        "viral": "🔥 Viral",
        "emotional": "❤️ Emotional",
        "funny": "😂 Funny",
        "storytelling": "📖 Storytelling",
        "best": "🏆 Best Moments",
    }.get(settings["style"], settings["style"])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🎬 Duration: {duration_text}",
                callback_data="menu_duration"
            )
        ],
        [
            InlineKeyboardButton(
                f"🔢 Clips: {settings['clips']}",
                callback_data="menu_clips"
            )
        ],
        [
            InlineKeyboardButton(
                f"📱 Format: {format_text}",
                callback_data="menu_format"
            )
        ],
        [
            InlineKeyboardButton(
                f"📝 Captions: {captions_text}",
                callback_data="toggle_captions"
            )
        ],
        [
            InlineKeyboardButton(
                f"🎯 Style: {style_text}",
                callback_data="menu_style"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Done",
                callback_data="settings_done"
            )
        ],
    ])


def duration_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("15 sec", callback_data="duration_15"),
            InlineKeyboardButton("30 sec", callback_data="duration_30"),
        ],
        [
            InlineKeyboardButton("45 sec", callback_data="duration_45"),
            InlineKeyboardButton("60 sec", callback_data="duration_60"),
        ],
        [
            InlineKeyboardButton(
                "✏️ Custom",
                callback_data="duration_custom"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="settings_back"
            )
        ],
    ])


def clips_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("3 clips", callback_data="clips_3"),
            InlineKeyboardButton("5 clips", callback_data="clips_5"),
        ],
        [
            InlineKeyboardButton("10 clips", callback_data="clips_10"),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="settings_back"
            )
        ],
    ])


def format_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📱 9:16 Reel",
                callback_data="format_9:16"
            )
        ],
        [
            InlineKeyboardButton(
                "⬜ 1:1",
                callback_data="format_1:1"
            ),
            InlineKeyboardButton(
                "🖥 16:9",
                callback_data="format_16:9"
            ),
        ],
        [
            InlineKeyboardButton(
                "Original",
                callback_data="format_original"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="settings_back"
            )
        ],
    ])


def style_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔥 Viral",
                callback_data="style_viral"
            ),
            InlineKeyboardButton(
                "❤️ Emotional",
                callback_data="style_emotional"
            ),
        ],
        [
            InlineKeyboardButton(
                "😂 Funny",
                callback_data="style_funny"
            ),
            InlineKeyboardButton(
                "📖 Storytelling",
                callback_data="style_storytelling"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏆 Best Moments",
                callback_data="style_best"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="settings_back"
            )
        ],
    ])


# --------------------------------------------------
# START
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    settings = get_settings(context)

    await update.message.reply_text(
        "👋 Welcome to ClipGenius AI!\n\n"
        "Configure your clips first:",
        reply_markup=settings_keyboard(settings)
    )


# --------------------------------------------------
# SETTINGS CALLBACKS
# --------------------------------------------------

async def settings_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    settings = get_settings(context)

    data = query.data

    # Duration menu
    if data == "menu_duration":

        await query.edit_message_text(
            "🎬 Choose clip duration:",
            reply_markup=duration_keyboard()
        )
        return

    # Clips menu
    if data == "menu_clips":

        await query.edit_message_text(
            "🔢 How many clips?",
            reply_markup=clips_keyboard()
        )
        return

    # Format menu
    if data == "menu_format":

        await query.edit_message_text(
            "📱 Choose video format:",
            reply_markup=format_keyboard()
        )
        return

    # Style menu
    if data == "menu_style":

        await query.edit_message_text(
            "🎯 Choose clip style:",
            reply_markup=style_keyboard()
        )
        return

    # Duration
    if data.startswith("duration_"):

        value = data.replace("duration_", "")

        if value == "custom":

            context.user_data["waiting_custom_duration"] = True

            await query.edit_message_text(
                "✏️ Send the duration in seconds.\n\n"
                "Example:\n"
                "25\n\n"
                "Maximum: 120 seconds."
            )

            return

        settings["duration"] = int(value)

        await query.edit_message_text(
            "⚙️ Settings",
            reply_markup=settings_keyboard(settings)
        )

        return

    # Number of clips
    if data.startswith("clips_"):

        settings["clips"] = int(
            data.replace("clips_", "")
        )

        await query.edit_message_text(
            "⚙️ Settings",
            reply_markup=settings_keyboard(settings)
        )

        return

    # Format
    if data.startswith("format_"):

        settings["format"] = data.replace(
            "format_",
            ""
        )

        await query.edit_message_text(
            "⚙️ Settings",
            reply_markup=settings_keyboard(settings)
        )

        return

    # Captions
    if data == "toggle_captions":

        settings["captions"] = not settings["captions"]

        await query.edit_message_text(
            "⚙️ Settings",
            reply_markup=settings_keyboard(settings)
        )

        return

    # Style
    if data.startswith("style_"):

        settings["style"] = data.replace(
            "style_",
            ""
        )

        await query.edit_message_text(
            "⚙️ Settings",
            reply_markup=settings_keyboard(settings)
        )

        return

    # Back
    if data == "settings_back":

        await query.edit_message_text(
            "⚙️ Settings",
            reply_markup=settings_keyboard(settings)
        )

        return

    # Done
    if data == "settings_done":

        await query.edit_message_text(
            "✅ Settings saved!\n\n"
            "Now send me your Google Drive video link."
        )

        return


# --------------------------------------------------
# CUSTOM DURATION
# --------------------------------------------------

async def handle_custom_duration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_custom_duration"
    ):
        return False

    text = update.message.text.strip()

    try:
        duration = int(text)

    except ValueError:

        await update.message.reply_text(
            "❌ Please enter only a number.\n"
            "Example: 30"
        )

        return True

    if duration < 5 or duration > 120:

        await update.message.reply_text(
            "❌ Duration must be between "
            "5 and 120 seconds."
        )

        return True

    settings = get_settings(context)

    settings["duration"] = duration

    context.user_data[
        "waiting_custom_duration"
    ] = False

    await update.message.reply_text(
        f"✅ Custom duration set to {duration} seconds.\n\n"
        "Send your Google Drive video link."
    )

    return True


# --------------------------------------------------
# DRIVE HANDLER
# --------------------------------------------------

async def handle_drive(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if await handle_custom_duration(
        update,
        context
    ):
        return

    text = update.message.text.strip()

    if "drive.google.com" not in text:

        await update.message.reply_text(
            "❌ Please send a valid Google Drive link."
        )

        return

    settings = get_settings(context)

    status = await update.message.reply_text(
        "⬇️ Downloading video..."
    )

    try:

        # ------------------------------------------
        # FILE ID
        # ------------------------------------------

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

        video_path = os.path.join(
            DOWNLOAD_FOLDER,
            f"{file_id}.mp4"
        )

        url = (
            f"https://drive.google.com/uc"
            f"?id={file_id}"
        )

        # ------------------------------------------
        # DOWNLOAD
        # ------------------------------------------

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
            "📝 Starting Whisper..."
        )

        # ------------------------------------------
        # WHISPER
        # ------------------------------------------

        segments = await asyncio.to_thread(
            transcribe,
            video_path
        )

        if not segments:

            raise RuntimeError(
                "Whisper found no speech."
            )

        transcript_file = os.path.join(
            DOWNLOAD_FOLDER,
            f"{file_id}_transcript.txt"
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

        # ------------------------------------------
        # GEMINI
        # ------------------------------------------

        await status.edit_text(
            "🤖 Gemini is finding the best moments..."
        )

        clips = await asyncio.to_thread(
            find_best_clips,
            segments,
            settings["clips"],
            settings["duration"],
            settings["style"]
        )

        if not clips:

            raise RuntimeError(
                "Gemini didn't find suitable clips."
            )

        await status.edit_text(
            f"✂️ Creating {len(clips)} clips..."
        )

        # ------------------------------------------
        # CREATE CLIPS
        # ------------------------------------------

        for index, clip in enumerate(
            clips,
            start=1
        ):

            clip_path = await asyncio.to_thread(
                create_clip,
                video_path,
                clip["start"],
                clip["end"],
                index,
                settings["format"],
                settings["captions"],
                segments
            )

            caption = (
                f"🔥 Viral Clip {index}\n\n"
                f"🎯 {clip.get('hook', '')}\n\n"
                f"💡 {clip.get('reason', '')}\n\n"
                f"⏱ {clip['start']:.1f}s → "
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
            f"✅ Finished!\n\n"
            f"🔥 {len(clips)} clips created."
        )

    except Exception as e:

        print(
            "ERROR:",
            repr(e)
        )

        await status.edit_text(
            f"❌ Error:\n{e}"
        )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

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
        CallbackQueryHandler(
            settings_callback
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
