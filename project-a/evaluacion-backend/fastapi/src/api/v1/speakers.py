from http import HTTPStatus
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from src.models.speaker_schema import SpeakerDetailOut, SpeakerOut
from src.providers.speaker_providers import get_speaker_service
from src.services.speaker_service import SpeakerService

router = APIRouter(prefix="/speakers", tags=["speakers"])

@router.get("/", response_model=list[SpeakerOut])
async def list_speakers(
    has_upcoming: bool = Query(False),
    service: SpeakerService = Depends(get_speaker_service),
):
    if has_upcoming:
        speakers = await service.get_speakers_with_upcoming()
    else:
        speakers = await service.get_all_speakers()
    
    return speakers

@router.get("/{speaker_id}", response_model=SpeakerDetailOut)
async def get_speaker_detail(
    speaker_id: UUID,
    service: SpeakerService = Depends(get_speaker_service),
):
    speaker = await service.get_speaker(speaker_id)

    if speaker is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="speaker not found")

    return speaker
