import os
import subprocess


OUTPUT_FOLDER = "clips"

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


def run_command(command):

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(
            result.stderr[-4000:]
        )

    return result


def get_video_duration(video_path):

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    result = run_command(command)

    try:
        return float(
            result.stdout.strip()
        )

    except ValueError:

        raise RuntimeError(
            "Could not determine video duration."
        )


def get_video_dimensions(video_path):

    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        video_path
    ]

    result = run_command(command)

    try:

        width, height = map(
            int,
            result.stdout.strip().split("x")
        )

        return width, height

    except Exception:

        raise RuntimeError(
            "Could not determine video dimensions."
        )


def get_video_filter(video_format):

    if video_format == "9:16":

        return (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        )

    if video_format == "1:1":

        return (
            "scale=1080:1080:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1080"
        )

    if video_format == "16:9":

        return (
            "scale=1920:1080:"
            "force_original_aspect_ratio=increase,"
            "crop=1920:1080"
        )

    return None


def create_clip(
    video_path,
    start,
    end,
    clip_number,
    video_format="original",
    captions=True,
    segments=None
):

    # -----------------------------------------
    # Get actual video duration
    # -----------------------------------------

    video_duration = get_video_duration(
        video_path
    )

    print(
        f"Video duration: "
        f"{video_duration:.2f}s"
    )

    # -----------------------------------------
    # Clamp timestamps
    # -----------------------------------------

    start = max(
        0.0,
        float(start)
    )

    end = min(
        float(end),
        video_duration
    )

    if start >= video_duration:

        raise RuntimeError(
            f"Clip starts after video ends: "
            f"{start:.2f}s"
        )

    if end <= start:

        raise RuntimeError(
            f"Invalid clip range: "
            f"{start:.2f} -> {end:.2f}"
        )

    duration = end - start

    # -----------------------------------------
    # Minimum duration protection
    # -----------------------------------------

    if duration < 3:

        end = min(
            start + 15,
            video_duration
        )

        duration = end - start

    if duration < 2:

        raise RuntimeError(
            "Selected clip is too short."
        )

    # -----------------------------------------
    # Output filename
    # -----------------------------------------

    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"viral_clip_{clip_number}.mp4"
    )

    # -----------------------------------------
    # Video filter
    # -----------------------------------------

    video_filter = get_video_filter(
        video_format
    )

    command = [
        "ffmpeg",
        "-y",

        "-ss",
        str(start),

        "-i",
        video_path,

        "-t",
        str(duration),

        "-map",
        "0:v:0",

        "-map",
        "0:a?",
    ]

    # -----------------------------------------
    # Video processing
    # -----------------------------------------

    if video_filter:

        command += [
            "-vf",
            video_filter
        ]

    command += [
        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        output_path
    ]

    print(
        f"Creating clip {clip_number}: "
        f"{start:.2f}s -> {end:.2f}s"
    )

    run_command(command)

    # -----------------------------------------
    # Verify output
    # -----------------------------------------

    if not os.path.exists(
        output_path
    ):

        raise RuntimeError(
            "FFmpeg did not create the clip."
        )

    size = os.path.getsize(
        output_path
    )

    if size < 10000:

        raise RuntimeError(
            "Generated clip is empty or invalid."
        )

    generated_duration = get_video_duration(
        output_path
    )

    print(
        f"Generated duration: "
        f"{generated_duration:.2f}s"
    )

    if generated_duration < 2:

        raise RuntimeError(
            "Generated clip is too short."
        )

    return output_path
