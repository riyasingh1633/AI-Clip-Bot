from faster_whisper import WhisperModel

print("Loading Whisper model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("Whisper model loaded!")


def transcribe(video_path):
    segments, info = model.transcribe(
        video_path,
        beam_size=5,
        vad_filter=True
    )

    results = []

    for segment in segments:
        text = segment.text.strip()

        if text:
            results.append({
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text
            })

    return results
