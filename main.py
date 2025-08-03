import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from murf import Murf

load_dotenv()  # Loads .env file

app = FastAPI()

class TTSRequest(BaseModel):
    text: str
    voice_id: str
    style: str = None  # Optional style field

api_key = os.getenv("MURF_API_KEY")
print("Loaded API key:", api_key)

@app.post("/api/tts")
def generate_tts(request: TTSRequest):
    try:
        client = Murf(api_key=api_key)
        # Add style if provided
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
        return {
            "success": False,
            "audio_url": None,
            "message": "Text-to-speech Conversion failed!",
            "error": str(e)
        }

@app.get("/api/tts/test")
def generate_test_tts():
    text = "This is day 2 of the 30 day build your own voice agent challenge"
    voice_id = "en-US-natalie"
    style = "Promo"
    try:
        client = Murf(api_key=api_key)
        res = client.text_to_speech.generate(
            text=text,
            voice_id=voice_id,
            format="MP3",
            channel_type="STEREO",
            sample_rate=44100,
            style=style  # If API supports style parameter
        )
        return {
            "success": True,
            "audio_url": res.audio_file,
            "message": "Text-to-speech Conversion successful!",
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "audio_url": None,
            "message": "Text-to-speech Conversion failed!",
            "error": str(e)
        }