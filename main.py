import os
import io
import logging
from typing import List, Dict
from fastapi import FastAPI, UploadFile, File, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from threading import Lock

from schemas.tts import TTSRequest, TTSResponse
from schemas.llm import LLMQueryRequest, LLMQueryResponse
from services.tts_service import murf_tts, murf_tts_chunked, get_fallback_audio
from services.stt_service import transcribe_audio
from services.llm_service import query_llm, format_history_for_gemini

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# NEW for Day 16: Directory for streamed audio
STREAMED_AUDIO_DIR = "streamed_audio"
os.makedirs(STREAMED_AUDIO_DIR, exist_ok=True)

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

# ---------- Conversation History ----------
chat_histories: Dict[str, List[Dict[str, str]]] = {}
chat_histories_lock = Lock()

# ---------- WebSocket Endpoint: Echo (retained for reference) ----------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"ECHO: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")

# ---------- NEW: WebSocket Audio Streaming Endpoint (Day 16) ----------
@app.websocket("/ws/stream")
async def websocket_audio_stream(websocket: WebSocket):
    await websocket.accept()
    # Simple: overwrite file each time; you can use session ID or timestamp for multiple files
    filename = os.path.join(STREAMED_AUDIO_DIR, "audio_stream.webm")
    with open(filename, "wb") as audio_file:
        try:
            while True:
                data = await websocket.receive()
                # Receive binary audio data (from MediaRecorder)
                if "bytes" in data:
                    audio_file.write(data["bytes"])
                # Optionally handle text (e.g. "close")
                elif "text" in data and data["text"] == "close":
                    break
        except WebSocketDisconnect:
            logger.info("WebSocket streaming connection closed")
        except Exception as e:
            logger.error(f"WebSocket audio streaming error: {e}")

# ---------- Endpoints ----------
@app.post("/api/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    try:
        result = await murf_tts_chunked(request)
        return result
    except Exception as e:
        logger.exception("TTS endpoint failed.")
        return TTSResponse(
            success=False,
            audio_url=get_fallback_audio(),
            audio_urls=[],
            message="Text-to-speech Conversion failed! Playing fallback audio.",
            error=str(e)
        )

@app.post("/api/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    try:
        file_location = os.path.join(UPLOAD_DIR, audio.filename)
        content = await audio.read()
        with open(file_location, "wb") as f:
            f.write(content)
        return {
            "name": audio.filename,
            "content_type": audio.content_type,
            "size": len(content)
        }
    except Exception as e:
        logger.exception("Audio upload failed.")
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
        text = await transcribe_audio(file)
        return {"transcript": text, "success": True}
    except Exception as e:
        logger.exception("Transcription failed.")
        fallback_url = get_fallback_audio()
        return {"transcript": "", "success": False, "error": str(e), "audio_url": fallback_url}

@app.post("/tts/echo", response_model=TTSResponse)
async def echo_bot(audio: UploadFile = File(...)):
    try:
        transcript = await transcribe_audio(audio)
        tts_req = TTSRequest(text=transcript)
        result = await murf_tts_chunked(tts_req)
        result.transcript = transcript
        result.message = "Echo bot Murf TTS generated!"
        return result
    except Exception as e:
        logger.exception("Echo bot failed.")
        fallback_url = get_fallback_audio()
        return TTSResponse(
            success=False,
            audio_url=fallback_url,
            audio_urls=[],
            message="Echo bot failed. Playing fallback audio.",
            error=str(e)
        )

@app.post("/llm/query", response_model=LLMQueryResponse)
async def llm_query(request: LLMQueryRequest):
    try:
        response = await query_llm(request)
        return response
    except Exception as e:
        logger.exception("LLM query failed.")
        fallback_url = get_fallback_audio()
        return LLMQueryResponse(
            success=False,
            response="",
            audio_url=fallback_url,
            audio_urls=[],
            transcript=request.text or "",
            error=str(e)
        )

@app.post("/agent/chat/{session_id}", response_model=LLMQueryResponse)
async def agent_chat(session_id: str, audio: UploadFile = File(...)):
    try:
        transcript = await transcribe_audio(audio)
        if not transcript:
            fallback_url = get_fallback_audio()
            return LLMQueryResponse(
                success=False,
                audio_url=fallback_url,
                error="No transcript from audio. Playing fallback audio."
            )

        with chat_histories_lock:
            history = chat_histories.get(session_id, [])
        history.append({"role": "user", "content": transcript})

        # Prepare chat history for LLM
        gemini_history = format_history_for_gemini(history)

        response = await query_llm(LLMQueryRequest(text=transcript), history=gemini_history)

        history.append({"role": "model", "content": response.response or ""})
        with chat_histories_lock:
            chat_histories[session_id] = history

        response.transcript = transcript
        return response
    except Exception as e:
        logger.exception("Agent chat failed")
        fallback_url = get_fallback_audio()
        return LLMQueryResponse(
            success=False,
            audio_url=fallback_url,
            error=str(e)
        )