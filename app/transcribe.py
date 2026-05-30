"""
Voice transcription using faster-whisper (runs locally, no API cost).
"""
import os
import tempfile
from typing import Optional

from loguru import logger

from app.config import WHISPER_MODEL

_model = None


def get_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
            _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            logger.info("Whisper model loaded")
        except ImportError:
            logger.warning("faster-whisper not installed. Voice messages will be skipped.")
            return None
    return _model


def transcribe(audio_bytes: bytes, file_ext: str = "ogg") -> Optional[str]:
    """
    Transcribe audio bytes to text.
    Telegram sends voice messages as .ogg (opus codec).
    """
    model = get_model()
    if model is None:
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        segments, info = model.transcribe(tmp_path, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()

        logger.info(f"Transcribed {info.duration:.1f}s audio → {len(text)} chars")
        return text if text else None

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
