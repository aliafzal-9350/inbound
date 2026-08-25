import os
import io
import tempfile
import asyncio
import logging
from typing import Tuple, Optional
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    @staticmethod
    async def download_media(media_url: str, access_token: Optional[str] = None) -> bytes:
        """Downloads audio/media bytes from Meta CDN or given URL."""
        headers = {}
        if access_token and "facebook.com" in media_url or "cdninstagram.com" in media_url:
            headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(media_url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            return resp.content

    @staticmethod
    async def transcode_to_16k_mono(audio_bytes: bytes, input_format: str = "ogg") -> bytes:
        """Asynchronously converts incoming audio (ogg/opus/m4a/mp3) to 16kHz mono WAV/MP3 using FFmpeg."""
        # Create temp files for ffmpeg
        with tempfile.NamedTemporaryFile(suffix=f".{input_format}", delete=False) as in_file:
            in_file.write(audio_bytes)
            in_path = in_file.name

        out_path = in_path + "_16k.wav"

        try:
            cmd = [
                "ffmpeg", "-y", "-i", in_path,
                "-ar", "16000", "-ac", "1",
                "-c:a", "pcm_s16le", out_path
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning(f"FFmpeg transcode failed ({stderr.decode('utf-8', errors='ignore')}), using original bytes.")
                return audio_bytes

            with open(out_path, "rb") as f:
                transcoded_bytes = f.read()
            return transcoded_bytes
        except Exception as e:
            logger.warning(f"FFmpeg not found or failed: {e}. Falling back to raw audio bytes.")
            return audio_bytes
        finally:
            for p in [in_path, out_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

    @staticmethod
    async def transcribe_groq_whisper(audio_bytes: bytes, filename: str = "audio.wav") -> Tuple[str, float]:
        """Transcribes audio using Groq Whisper Large-v3 API (`whisper-large-v3`).
        Returns (transcript_text, confidence_score)."""
        groq_api_key = settings.GROQ_API_KEY
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not configured. Returning mock transcription.")
            return "Salam mujhe appointment leni hai", 0.95

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {
                    "file": (filename, audio_bytes, "audio/wav"),
                    "model": (None, settings.GROQ_WHISPER_MODEL),
                    "temperature": (None, "0.0"),
                    "response_format": (None, "verbose_json"),
                }
                headers = {"Authorization": f"Bearer {groq_api_key}"}
                resp = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                )
                resp.raise_for_status()
                data = resp.json()

                text = data.get("text", "").strip()
                # Calculate average segment or token confidence if available
                confidence = 0.92
                segments = data.get("segments", [])
                if segments:
                    avg_logprob = sum(s.get("avg_logprob", -0.2) for s in segments) / len(segments)
                    # Convert avg_logprob to approximate confidence (0.0 to 1.0)
                    import math
                    confidence = min(1.0, max(0.1, math.exp(avg_logprob)))

                return text, confidence
        except Exception as e:
            logger.error(f"Groq Whisper transcription failed: {e}")
            return "", 0.0

    @classmethod
    async def process_voice_note(cls, audio_bytes: bytes, mime_type: str = "audio/ogg") -> Tuple[str, float, bool]:
        """Complete audio pipeline:
        1. Transcode to 16kHz mono WAV
        2. Stream to Groq Whisper Large-v3
        3. Evaluate confidence score. If < 0.65, flags for recovery.
        Returns: (transcript, confidence, needs_human_recovery)
        """
        fmt = "ogg"
        if "mp4" in mime_type or "m4a" in mime_type:
            fmt = "m4a"
        elif "mp3" in mime_type:
            fmt = "mp3"
        elif "wav" in mime_type:
            fmt = "wav"

        normalized_bytes = await cls.transcode_to_16k_mono(audio_bytes, input_format=fmt)
        transcript, confidence = await cls.transcribe_groq_whisper(normalized_bytes)

        needs_human_recovery = confidence < 0.65 or not transcript
        return transcript, confidence, needs_human_recovery
