import io
import os
import assemblyai as aai
from dotenv import load_dotenv

from .utils import sanitize_text

load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

async def transcribe_audio(file) -> str:
    audio_bytes = await file.read()
    aai.settings.api_key = ASSEMBLYAI_API_KEY
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(io.BytesIO(audio_bytes))
    return sanitize_text(transcript.text or "")