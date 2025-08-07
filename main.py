import os
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf
import assemblyai as aai

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

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-natalie"
    style: str = "Promo"

api_key = os.getenv("MURF_API_KEY")
print("Loaded Murf API key:", api_key)

@app.post("/api/tts")
async def generate_tts(request: TTSRequest):
    try:
        client = Murf(api_key=api_key)
        params = {
            "text": request.text,
            "voice_id": request.voice_id,
            "format": "MP3",
            "channel_type": "STEREO",
            "sample_rate": 44100,
        }
        if request.style:
            params["style"] = request.style
        res = client.text_to_speech.generate(**params)
        return {
            "success": True,
            "audio_url": res.audio_file,
            "message": "Text-to-speech Conversion successful!",
            "error": None
        }
    except Exception as e:
        print("Error in /api/tts:", e)
        return {
            "success": False,
            "audio_url": None,
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


# === NEW ENDPOINT: /transcribe/file ===
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    print("WARNING: ASSEMBLYAI_API_KEY not found in .env!")

@app.post("/transcribe/file")
async def transcribe_file(file: UploadFile = File(...)):
    try:
        # Read the file contents directly
        audio_bytes = await file.read()
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        # AssemblyAI SDK accepts file-like objects, so wrap in BytesIO
        import io
        transcript = transcriber.transcribe(io.BytesIO(audio_bytes))
        return {"transcript": transcript.text, "success": True}
    except Exception as e:
        print("Error in /transcribe/file:", e)
        return {"transcript": "", "success": False, "error": str(e)}