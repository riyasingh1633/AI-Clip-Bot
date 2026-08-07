from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Union


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class VideoEditorError(Exception):
    """Custom exception for video editing errors."""


class VideoEditor:
    def __init__(self, ffmpeg_binary: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_binary
        self._verify_ffmpeg()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def create_clips(
        self,
        video_path: Union[str, Path],
        timestamps: Union[str, Path, Dict[str, Any], List[Dict[str, Any]]],
        output_dir: Union[str, Path] = "output",
    ) -> List[str]:
        """
        Create clips from timestamps.

        Parameters
        ----------
        video_path:
            Original video.

        timestamps:
            JSON file path
            JSON string
            dict
            list

        output_dir:
            Folder where clips will be saved.

        Returns
        -------
        List[str]
            Paths of generated clips.
        """

        video_path = Path(video_path)

        if not video_path.exists():
            raise VideoEditorError(f"Video not found: {video_path}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamps = self._load_timestamps(timestamps)

        if not timestamps:
            raise VideoEditorError("No timestamps found.")

        created = []

        for index, clip in enumerate(timestamps, start=1):
            try:
                start = self._extract_start(clip)
                end = self._extract_end(clip)

                if end <= start:
                    logger.warning(
                        "Skipping clip %d because end <= start.",
                        index,
                    )
                    continue

                filename = f"clip_{index:03d}.mp4"
                destination = output_dir / filename

                self._cut_video(
                    input_video=video_path,
                    output_video=destination,
                    start=start,
                    end=end,
                )

                created.append(str(destination))

                logger.info("Created %s", destination)

            except Exception as exc:
                logger.exception(
                    "Failed creating clip %d: %s",
                    index,
                    exc,
                )

        return created

    # ------------------------------------------------------------------ #
    # Timestamp Parsing
    # ------------------------------------------------------------------ #

    def _load_timestamps(
        self,
        data: Union[str, Path, Dict[str, Any], List[Any]],
    ) -> List[Dict[str, Any]]:

        if isinstance(data, Path):
            if not data.exists():
                raise VideoEditorError(f"JSON not found: {data}")

            with open(data, "r", encoding="utf-8") as f:
                data = json.load(f)

        elif isinstance(data, str):
            possible_path = Path(data)

            if possible_path.exists():
                with open(possible_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(data)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            for key in (
                "clips",
                "timestamps",
                "segments",
                "results",
                "highlights",
            ):
                if key in data and isinstance(data[key], list):
                    return data[key]

            return [data]

        raise VideoEditorError("Unsupported timestamp JSON.")

    def _extract_start(self, clip: Dict[str, Any]) -> float:

        keys = (
            "start",
            "start_time",
            "start_seconds",
            "from",
        )

        for key in keys:
            if key in clip:
                return self._parse_time(clip[key])

        raise VideoEditorError("Missing clip start time.")

    def _extract_end(self, clip: Dict[str, Any]) -> float:

        keys = (
            "end",
            "end_time",
            "end_seconds",
            "to",
        )

        for key in keys:
            if key in clip:
                return self._parse_time(clip[key])

        raise VideoEditorError("Missing clip end time.")

    # ------------------------------------------------------------------ #
    # Time Parsing
    # ------------------------------------------------------------------ #

    def _parse_time(self, value: Any) -> float:

        if isinstance(value, (float, int)):
            return float(value)

        if isinstance(value, str):

            value = value.strip()

            if value.replace(".", "", 1).isdigit():
                return float(value)

            parts = value.split(":")

            try:

                if len(parts) == 3:
                    h, m, s = parts
                    return (
                        int(h) * 3600
                        + int(m) * 60
                        + float(s)
                    )

                if len(parts) == 2:
                    m, s = parts
                    return int(m) * 60 + float(s)

            except Exception:
                pass

        raise VideoEditorError(f"Invalid timestamp: {value}")

    # ------------------------------------------------------------------ #
    # FFmpeg
    # ------------------------------------------------------------------ #

    def _verify_ffmpeg(self):

        if shutil.which(self.ffmpeg) is None:
            raise VideoEditorError(
                "FFmpeg not found. Install FFmpeg first."
            )

    def _cut_video(
        self,
        input_video: Path,
        output_video: Path,
        start: float,
        end: float,
    ):

        duration = end - start

        copy_cmd = [
            self.ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start),
            "-i",
            str(input_video),
            "-t",
            str(duration),
            "-avoid_negative_ts",
            "make_zero",
            "-c",
            "copy",
            str(output_video),
        ]

        result = subprocess.run(
            copy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if (
            result.returncode == 0
            and output_video.exists()
            and output_video.stat().st_size > 0
        ):
            return

        logger.info("Falling back to re-encoding...")

        encode_cmd = [
            self.ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start),
            "-i",
            str(input_video),
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output_video),
        ]

        result = subprocess.run(
            encode_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            raise VideoEditorError(result.stderr.strip())

        if (
            not output_video.exists()
            or output_video.stat().st_size == 0
        ):
            raise VideoEditorError(
                "FFmpeg completed but output file was not created."
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create video clips from Gemini timestamps."
    )

    parser.add_argument(
        "video",
        help="Path to source video",
    )

    parser.add_argument(
        "timestamps",
        help="JSON file or JSON string",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="Output directory",
    )

    args = parser.parse_args()

    editor = VideoEditor()

    clips = editor.create_clips(
        video_path=args.video,
        timestamps=args.timestamps,
        output_dir=args.output,
    )

    print("\nGenerated clips:\n")

    for clip in clips:
        print(clip)
