from pydantic import BaseModel
from typing import List, Optional

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-natalie"
    style: str = "Promo"

class TTSResponse(BaseModel):
    success: bool
    audio_url: Optional[str] = None
    audio_urls: List[str] = []
    message: Optional[str] = None
    error: Optional[str] = None
    transcript: Optional[str] = None