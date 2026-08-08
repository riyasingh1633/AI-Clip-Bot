import os
import subprocess


OUTPUT_FOLDER = "clips"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def create_clip(video_path, start, end, clip_number):

    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"viral_clip_{clip_number}.mp4"
    )

    duration = end - start

    command = [
        "ffmpeg",
        "-y",

        "-ss",
        str(start),

        "-i",
        video_path,

        "-t",
        str(duration),

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-c:a",
        "aac",

        "-movflags",
        "+faststart",

        output_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed:\n" + result.stderr[-2000:]
        )

    if not os.path.exists(output_path):
        raise RuntimeError("Clip was not created.")

    return output_path
