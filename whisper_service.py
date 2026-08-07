from faster_whisper import WhisperModel

# Load the model only once
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

def transcribe_video(video_path):
    """
    Transcribe a video/audio file.
    Returns:
        transcript (str)
        duration (float)
    """

    segments, info = model.transcribe(
        video_path,
        beam_size=5,
        vad_filter=True
    )

    transcript = ""

    for segment in segments:
        transcript += segment.text + " "

    return transcript.strip(), info.duration
