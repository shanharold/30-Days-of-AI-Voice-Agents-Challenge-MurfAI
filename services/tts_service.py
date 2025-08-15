import os
from typing import List, Optional
from murf import Murf
from dotenv import load_dotenv

from schemas.tts import TTSRequest, TTSResponse
from .utils import sanitize_text, split_into_chunks

load_dotenv()
MURF_API_KEY = os.getenv("MURF_API_KEY")
MAX_MURF_LEN = 3000

def murf_tts(text: str, voice_id: str = "en-US-natalie", style: str = "Promo") -> str:
    client = Murf(api_key=MURF_API_KEY)
    params = {
        "text": text,
        "voice_id": voice_id,
        "format": "MP3",
        "channel_type": "STEREO",
        "sample_rate": 44100
    }
    if style:
        params["style"] = style
    res = client.text_to_speech.generate(**params)
    return res.audio_file

async def murf_tts_chunked(request: TTSRequest) -> TTSResponse:
    clean_text = sanitize_text(request.text or "")
    if not clean_text:
        return TTSResponse(
            success=False,
            audio_url=None,
            audio_urls=[],
            message="No text provided.",
            error="EMPTY_TEXT"
        )
    if len(clean_text) > MAX_MURF_LEN:
        parts = split_into_chunks(clean_text, MAX_MURF_LEN)
        urls = [murf_tts(part, request.voice_id, request.style) for part in parts]
        return TTSResponse(
            success=True,
            audio_url=None,
            audio_urls=urls,
            message=f"Generated {len(urls)} audio segments via Murf.",
            error=None
        )
    else:
        audio_url = murf_tts(clean_text, request.voice_id, request.style)
        return TTSResponse(
            success=True,
            audio_url=audio_url,
            audio_urls=[],
            message="Text-to-speech Conversion successful!",
            error=None
        )

def get_fallback_audio():
    try:
        return murf_tts("I'm having trouble connecting right now. Please try again later.", "en-US-natalie", "Promo")
    except Exception:
        return None