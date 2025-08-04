import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf

load_dotenv()

app = FastAPI()

# Serve static files at /static
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

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
print("Loaded API key:", api_key)

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
        print("Error in /api/tts:", e)  # DEBUG
        return {
            "success": False,
            "audio_url": None,
            "message": "Text-to-speech Conversion failed!",
            "error": str(e)
        }