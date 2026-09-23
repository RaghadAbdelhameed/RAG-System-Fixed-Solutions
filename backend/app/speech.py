"""
Voice-query support: transcribes uploaded audio to text using faster-whisper,
so a user can speak their question instead of typing it.
"""
from functools import lru_cache

from .config import settings


@lru_cache(maxsize=1)
def get_whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel(settings.WHISPER_MODEL, device=settings.WHISPER_DEVICE)


def transcribe_audio(file_path: str) -> str:
    model = get_whisper_model()
    segments, _info = model.transcribe(file_path)
    return " ".join(seg.text.strip() for seg in segments).strip()
