import os
from dotenv import load_dotenv
from schemas.llm import LLMQueryRequest, LLMQueryResponse
from .tts_service import murf_tts, murf_tts_chunked, get_fallback_audio
from .utils import sanitize_text, clamp_text

# Gemini API
try:
    from google.generativeai import GenerativeModel, configure
except ImportError:
    GenerativeModel = None
    configure = None

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAX_LLM_LEN = 3000
MAX_MURF_LEN = 3000

def format_history_for_gemini(history):
    # Converts [{role, content}] to Gemini's history format
    return [{"role": msg["role"], "parts": [msg["content"]]} for msg in history]

async def query_llm(request: LLMQueryRequest, history=None) -> LLMQueryResponse:
    text = sanitize_text(request.text or "")
    received_len = len(text)
    if not text:
        return LLMQueryResponse(
            success=False,
            response="",
            audio_url=None,
            audio_urls=[],
            transcript="",
            error="No text provided for LLM query."
        )
    clamped_text = clamp_text(text, MAX_LLM_LEN)
    if GenerativeModel is None or configure is None or not GEMINI_API_KEY:
        fallback_url = get_fallback_audio()
        return LLMQueryResponse(
            success=False,
            response="",
            audio_url=fallback_url,
            audio_urls=[],
            transcript=clamped_text,
            error="Gemini API not available. Playing fallback audio."
        )
    configure(api_key=GEMINI_API_KEY)
    model = GenerativeModel("gemini-2.5-pro")
    chat = model.start_chat(history=history if history else [])
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
            return LLMQueryResponse(
                success=False,
                response="",
                audio_url=fallback_url,
                audio_urls=[],
                transcript=clamped_text,
                error="LLM did not produce a response. Playing fallback audio."
            )
    except Exception as e:
        fallback_url = get_fallback_audio()
        return LLMQueryResponse(
            success=False,
            response="",
            audio_url=fallback_url,
            audio_urls=[],
            transcript=clamped_text,
            error=f"LLM query failed: {e}. Playing fallback audio."
        )
    try:
        if len(llm_text) > MAX_MURF_LEN:
            tts_req = LLMQueryRequest(text=llm_text)
            tts_result = await murf_tts_chunked(tts_req)
            return LLMQueryResponse(
                success=True,
                response=llm_text,
                audio_url=None,
                audio_urls=tts_result.audio_urls,
                transcript=clamped_text,
                error=None
            )
        else:
            audio_url = murf_tts(llm_text, "en-US-natalie", "Promo")
            return LLMQueryResponse(
                success=True,
                response=llm_text,
                audio_url=audio_url,
                audio_urls=[],
                transcript=clamped_text,
                error=None
            )
    except Exception as e:
        fallback_url = get_fallback_audio()
        return LLMQueryResponse(
            success=True,
            response=llm_text,
            audio_url=fallback_url,
            audio_urls=[],
            transcript=clamped_text,
            error=f"TTS failed: {e}. Playing fallback audio."
        )