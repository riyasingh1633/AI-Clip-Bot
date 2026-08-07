from faster_whisper import WhisperModel

# Load Whisper model once
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

def transcribe(video_path):
    segments, info = model.transcribe(
        video_path,
        beam_size=5,
        vad_filter=True
    )

    transcript = ""

    for segment in segments:
        transcript += segment.text + "\n"

    return transcript
