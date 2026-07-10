from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.ai.voice_adapter import get_stt_provider, get_tts_provider
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/voice", tags=["voice"])


class TranscriptResponse(BaseModel):
    transcript: str


class TTSRequest(BaseModel):
    text: str


@router.post("/stt", response_model=TranscriptResponse)
async def speech_to_text(file: UploadFile, current_user: User = Depends(get_current_user)):
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file")

    provider = get_stt_provider()
    transcript = await provider.transcribe(audio_bytes, file.filename or "audio.webm", file.content_type or "audio/webm")
    return TranscriptResponse(transcript=transcript)


@router.post("/tts")
async def text_to_speech(payload: TTSRequest, current_user: User = Depends(get_current_user)):
    provider = get_tts_provider()
    audio_bytes = await provider.synthesize(payload.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")
