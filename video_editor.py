import os
import subprocess


OUTPUT_FOLDER = "clips"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_video_duration(video_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFprobe failed:\n" + result.stderr[-2000:]
        )

    try:
        return float(result.stdout.strip())
    except ValueError:
        raise RuntimeError("Could not determine video duration.")


def create_clip(video_path, start, end, clip_number):

    video_duration = get_video_duration(video_path)

    print(f"Video duration: {video_duration:.2f}s")
    print(f"Requested clip: {start:.2f}s -> {end:.2f}s")

    # Safety limits
    start = max(0.0, float(start))
    end = min(float(end), video_duration)

    # Make sure start is inside the video
    if start >= video_duration:
        raise RuntimeError(
            f"Clip start {start:.2f}s is beyond "
            f"video duration {video_duration:.2f}s."
        )

    # Minimum useful duration
    if end - start < 3:
        end = min(
            start + 15,
            video_duration
        )

    if end <= start:
        raise RuntimeError(
            f"Invalid clip range: {start:.2f} -> {end:.2f}"
        )

    duration = end - start

    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"viral_clip_{clip_number}.mp4"
    )

    print(
        f"Creating clip {clip_number}: "
        f"{start:.2f}s -> {end:.2f}s "
        f"({duration:.2f}s)"
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
            "FFmpeg failed:\n" +
            result.stderr[-3000:]
        )

    if not os.path.exists(output_path):
        raise RuntimeError(
            "Clip was not created."
        )

    if os.path.getsize(output_path) < 10000:
        raise RuntimeError(
            "FFmpeg created an invalid/empty clip."
        )

    # Verify the generated clip
    generated_duration = get_video_duration(
        output_path
    )

    print(
        f"Generated clip duration: "
        f"{generated_duration:.2f}s"
    )

    if generated_duration < 2:
        raise RuntimeError(
            f"Generated clip is too short: "
            f"{generated_duration:.2f}s"
        )

    return output_path
