import os
import io
from typing import List

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf
import assemblyai as aai

# Import Gemini API
try:
    from google.generativeai import GenerativeModel, configure
except ImportError:
    GenerativeModel = None
    configure = None

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def main():
    return FileResponse("static/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Config / Constants ----------
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MAX_LLM_LEN = 3000            # What we send to Gemini
MAX_MURF_LEN = 3000           # Murf /v1/speech/generate limit

# ---------- Models ----------
class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-natalie"
    style: str = "Promo"

class LLMQueryRequest(BaseModel):
    text: str | None = None

# ---------- Utilities ----------
def sanitize_text(s: str) -> str:
    # Ensure it's a string and normalize whitespace
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\r", " ").replace("\n", " ")
    s = " ".join(s.split())
    return s.strip()

def clamp_text(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len]

def split_into_chunks(text: str, max_len: int) -> List[str]:
    """
    Splits text into chunks no longer than max_len, breaking on word boundaries
    when possible.
    """
    text = text.strip()
    if len(text) <= max_len:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        if end < len(text):
            # try to break on the last space within the window
            space = text.rfind(" ", start, end)
            if space != -1 and space > start:
                end = space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks if chunks else [""]

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

def murf_tts_chunked(text: str, voice_id: str = "en-US-natalie", style: str = "Promo") -> List[str]:
    """
    Splits text into <= MAX_MURF_LEN char chunks and generates a Murf audio file for each chunk.
    Returns a list of audio URLs in order.
    """
    clean = sanitize_text(text)
    parts = split_into_chunks(clean, MAX_MURF_LEN)
    urls = []
    for idx, part in enumerate(parts, start=1):
        url = murf_tts(part, voice_id=voice_id, style=style)
        urls.append(url)
    return urls

# ---------- Endpoints ----------

@app.post("/api/tts")
async def generate_tts(request: TTSRequest):
    try:
        clean_text = sanitize_text(request.text or "")
        if not clean_text:
            return {
                "success": False,
                "audio_url": None,
                "audio_urls": [],
                "message": "No text provided.",
                "error": "EMPTY_TEXT"
            }

        # Use chunked generation if longer than Murf's 3000 char limit
        if len(clean_text) > MAX_MURF_LEN:
            urls = murf_tts_chunked(clean_text, request.voice_id, request.style)
            return {
                "success": True,
                "audio_url": None,
                "audio_urls": urls,
                "message": f"Generated {len(urls)} audio segments via Murf.",
                "error": None
            }
        else:
            audio_url = murf_tts(clean_text, request.voice_id, request.style)
            return {
                "success": True,
                "audio_url": audio_url,
                "audio_urls": [],
                "message": "Text-to-speech Conversion successful!",
                "error": None
            }
    except Exception as e:
        return {
            "success": False,
            "audio_url": None,
            "audio_urls": [],
            "message": "Text-to-speech Conversion failed!",
            "error": str(e)
        }

@app.post("/api/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, audio.filename)
    with open(file_location, "wb") as f:
        content = await audio.read()
        f.write(content)
    return {
        "name": audio.filename,
        "content_type": audio.content_type,
        "size": len(content)
    }

@app.post("/transcribe/file")
async def transcribe_file(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(io.BytesIO(audio_bytes))
        text = sanitize_text(transcript.text or "")
        return {"transcript": text, "success": True}
    except Exception as e:
        return {"transcript": "", "success": False, "error": str(e)}

@app.post("/tts/echo")
async def echo_bot(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(io.BytesIO(audio_bytes))
        transcript_text = sanitize_text(transcript.text or "")

        urls = murf_tts_chunked(transcript_text, "en-US-natalie", "Promo")

        return JSONResponse(content={
            "success": True,
            "audio_url": urls[0] if len(urls) == 1 else None,
            "audio_urls": urls if len(urls) > 1 else [],
            "transcript": transcript_text,
            "message": "Echo bot Murf TTS generated!"
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "audio_url": None,
            "audio_urls": [],
            "transcript": "",
            "message": "Echo bot failed.",
            "error": str(e)
        })

@app.post("/llm/query")
async def llm_query(request: Request):
    try:
        # STRICT: Accept ONLY JSON {text: "..."}
        body = await request.json()
        raw_text = body.get("text", "")
        text = sanitize_text(raw_text)
        received_len = len(text)

        if not text:
            return JSONResponse(content={
                "success": False,
                "response": "",
                "audio_url": None,
                "audio_urls": [],
                "transcript": "",
                "error": "No text provided for LLM query."
            })

        # Clamp what we send to Gemini
        clamped_text = clamp_text(text, MAX_LLM_LEN)
        print(f"[LLM QUERY] Received length={received_len}, sending length={len(clamped_text)}")

        if GenerativeModel is None or configure is None or not GEMINI_API_KEY:
            return JSONResponse(content={
                "success": False,
                "response": "",
                "audio_url": None,
                "audio_urls": [],
                "transcript": clamped_text,
                "error": "Gemini API not available."
            })

        configure(api_key=GEMINI_API_KEY)
        model = GenerativeModel("gemini-2.5-pro")
        chat = model.start_chat(history=[])

        try:
            gemini_response = chat.send_message(clamped_text)

            # Robust extraction from Gemini response
            llm_text = ""
            if hasattr(gemini_response, "text") and gemini_response.text:
                llm_text = gemini_response.text
            elif hasattr(gemini_response, "candidates") and gemini_response.candidates:
                candidate = gemini_response.candidates[0]
                content = getattr(candidate, "content", None)
                if content and getattr(content, "parts", None):
                    part0 = content.parts[0]
                    llm_text = getattr(part0, "text", "") or getattr(part0, "data", "") or ""
            else:
                llm_text = str(gemini_response)

            llm_text = sanitize_text(llm_text)
            if not llm_text:
                return JSONResponse(content={
                    "success": False,
                    "response": "",
                    "audio_url": None,
                    "audio_urls": [],
                    "transcript": clamped_text,
                    "error": "LLM did not produce a response. Try a longer or different prompt."
                })
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "response": "",
                "audio_url": None,
                "audio_urls": [],
                "transcript": clamped_text,
                "error": f"LLM query failed: {e}"
            })

        # Generate Murf audio, chunking if needed (3000 char limit)
        try:
            if len(llm_text) > MAX_MURF_LEN:
                urls = murf_tts_chunked(llm_text, "en-US-natalie", "Promo")
                return JSONResponse(content={
                    "success": True,
                    "response": llm_text,
                    "audio_url": None,
                    "audio_urls": urls,
                    "transcript": clamped_text,
                    "error": None
                })
            else:
                audio_url = murf_tts(llm_text, "en-US-natalie", "Promo")
                return JSONResponse(content={
                    "success": True,
                    "response": llm_text,
                    "audio_url": audio_url,
                    "audio_urls": [],
                    "transcript": clamped_text,
                    "error": None
                })
        except Exception as e:
            # Return LLM text even if TTS fails
            return JSONResponse(content={
                "success": True,
                "response": llm_text,
                "audio_url": None,
                "audio_urls": [],
                "transcript": clamped_text,
                "error": f"TTS failed: {e}"
            })

    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "response": "",
            "audio_url": None,
            "audio_urls": [],
            "transcript": "",
            "error": str(e)
        })