import os
import io
from typing import List, Dict
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf
import assemblyai as aai
from threading import Lock

# Gemini API
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
MAX_LLM_LEN = 3000
MAX_MURF_LEN = 3000

# ---------- Models ----------
class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-natalie"
    style: str = "Promo"

class LLMQueryRequest(BaseModel):
    text: str | None = None

# ---------- Utilities ----------
def sanitize_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\r", " ").replace("\n", " ")
    s = " ".join(s.split())
    return s.strip()

def clamp_text(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len]

def split_into_chunks(text: str, max_len: int) -> List[str]:
    text = text.strip()
    if len(text) <= max_len:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        if end < len(text):
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
    clean = sanitize_text(text)
    parts = split_into_chunks(clean, MAX_MURF_LEN)
    urls = []
    for idx, part in enumerate(parts, start=1):
        url = murf_tts(part, voice_id=voice_id, style=style)
        urls.append(url)
    return urls

# ---------- Fallback Audio ----------
def get_fallback_audio():
    try:
        # Try to generate fallback audio using Murf
        return murf_tts("I'm having trouble connecting right now. Please try again later.", "en-US-natalie", "Promo")
    except Exception:
        # If Murf fails, just return None (client can handle a local fallback)
        return None

# ---------- Conversation History ----------
chat_histories: Dict[str, List[Dict[str, str]]] = {}
chat_histories_lock = Lock()

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
        fallback_url = get_fallback_audio()
        return {
            "success": False,
            "audio_url": fallback_url,
            "audio_urls": [],
            "message": "Text-to-speech Conversion failed! Playing fallback audio.",
            "error": str(e)
        }

@app.post("/api/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    try:
        file_location = os.path.join(UPLOAD_DIR, audio.filename)
        with open(file_location, "wb") as f:
            content = await audio.read()
            f.write(content)
        return {
            "name": audio.filename,
            "content_type": audio.content_type,
            "size": len(content)
        }
    except Exception as e:
        fallback_url = get_fallback_audio()
        return {
            "success": False,
            "audio_url": fallback_url,
            "message": "Audio upload failed! Playing fallback audio.",
            "error": str(e)
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
        fallback_url = get_fallback_audio()
        return {"transcript": "", "success": False, "error": str(e), "audio_url": fallback_url}

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
        fallback_url = get_fallback_audio()
        return JSONResponse(content={
            "success": False,
            "audio_url": fallback_url,
            "audio_urls": [],
            "transcript": "",
            "message": "Echo bot failed. Playing fallback audio.",
            "error": str(e)
        })

@app.post("/llm/query")
async def llm_query(request: Request):
    try:
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
        clamped_text = clamp_text(text, MAX_LLM_LEN)
        print(f"[LLM QUERY] Received length={received_len}, sending length={len(clamped_text)}")
        if GenerativeModel is None or configure is None or not GEMINI_API_KEY:
            fallback_url = get_fallback_audio()
            return JSONResponse(content={
                "success": False,
                "response": "",
                "audio_url": fallback_url,
                "audio_urls": [],
                "transcript": clamped_text,
                "error": "Gemini API not available. Playing fallback audio."
            })
        configure(api_key=GEMINI_API_KEY)
        model = GenerativeModel("gemini-2.5-pro")
        chat = model.start_chat(history=[])
        try:
            gemini_response = chat.send_message(clamped_text)
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
                fallback_url = get_fallback_audio()
                return JSONResponse(content={
                    "success": False,
                    "response": "",
                    "audio_url": fallback_url,
                    "audio_urls": [],
                    "transcript": clamped_text,
                    "error": "LLM did not produce a response. Playing fallback audio."
                })
        except Exception as e:
            fallback_url = get_fallback_audio()
            return JSONResponse(content={
                "success": False,
                "response": "",
                "audio_url": fallback_url,
                "audio_urls": [],
                "transcript": clamped_text,
                "error": f"LLM query failed: {e}. Playing fallback audio."
            })
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
            fallback_url = get_fallback_audio()
            return JSONResponse(content={
                "success": True,
                "response": llm_text,
                "audio_url": fallback_url,
                "audio_urls": [],
                "transcript": clamped_text,
                "error": f"TTS failed: {e}. Playing fallback audio."
            })
    except Exception as e:
        fallback_url = get_fallback_audio()
        return JSONResponse(content={
            "success": False,
            "response": "",
            "audio_url": fallback_url,
            "audio_urls": [],
            "transcript": "",
            "error": str(e)
        })

# ---------- Day 10: Conversational Chat Endpoint ----------
@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str, audio: UploadFile = File(...)):
    try:
        # 1. STT
        audio_bytes = await audio.read()
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(io.BytesIO(audio_bytes))
        user_text = sanitize_text(transcript.text or "")

        if not user_text:
            fallback_url = get_fallback_audio()
            return JSONResponse(content={
                "success": False,
                "audio_url": fallback_url,
                "error": "No transcript from audio. Playing fallback audio."
            })

        # 2. Get/Create chat history for session
        with chat_histories_lock:
            history = chat_histories.get(session_id, [])

        # 3. Append user message
        history.append({"role": "user", "content": user_text})

        # 4. Prepare Gemini format
        gemini_history = [
            {"role": msg["role"], "parts": [msg["content"]]}
            for msg in history
        ]

        # 5. LLM response
        if GenerativeModel is None or configure is None or not GEMINI_API_KEY:
            fallback_url = get_fallback_audio()
            return JSONResponse(content={
                "success": False,
                "audio_url": fallback_url,
                "error": "Gemini API not available. Playing fallback audio."
            })
        configure(api_key=GEMINI_API_KEY)
        model = GenerativeModel("gemini-2.5-pro")
        chat = model.start_chat(history=gemini_history)

        try:
            gemini_response = chat.send_message(user_text)
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
        except Exception as e:
            fallback_url = get_fallback_audio()
            return JSONResponse(content={
                "success": False,
                "audio_url": fallback_url,
                "error": f"LLM query failed: {e}. Playing fallback audio."
            })

        # 6. Append LLM response to history
        history.append({"role": "model", "content": llm_text})

        # 7. Save updated history
        with chat_histories_lock:
            chat_histories[session_id] = history

        # 8. TTS
        try:
            if len(llm_text) > MAX_MURF_LEN:
                urls = murf_tts_chunked(llm_text, "en-US-natalie", "Promo")
                return JSONResponse(content={
                    "success": True,
                    "audio_url": None,
                    "audio_urls": urls,
                    "response": llm_text,
                    "transcript": user_text,
                })
            else:
                audio_url = murf_tts(llm_text, "en-US-natalie", "Promo")
                return JSONResponse(content={
                    "success": True,
                    "audio_url": audio_url,
                    "audio_urls": [],
                    "response": llm_text,
                    "transcript": user_text,
                })
        except Exception as e:
            fallback_url = get_fallback_audio()
            return JSONResponse(content={
                "success": True,
                "audio_url": fallback_url,
                "audio_urls": [],
                "response": llm_text,
                "transcript": user_text,
                "error": f"TTS failed: {e}. Playing fallback audio."
            })
    except Exception as e:
        fallback_url = get_fallback_audio()
        return JSONResponse(content={
            "success": False,
            "audio_url": fallback_url,
            "error": str(e)
        })