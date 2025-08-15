from pydantic import BaseModel
from typing import List, Optional

class LLMQueryRequest(BaseModel):
    text: Optional[str] = None

class LLMQueryResponse(BaseModel):
    success: bool
    response: str = ""
    audio_url: Optional[str] = None
    audio_urls: List[str] = []
    transcript: Optional[str] = ""
    error: Optional[str] = None