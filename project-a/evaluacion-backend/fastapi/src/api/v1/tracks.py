from fastapi import APIRouter, Depends
from src.models.track_schema import TrackListOut
from src.providers.track_providers import get_track_service
from src.services.track_service import TrackService

router = APIRouter(prefix="/tracks", tags=["tracks"])

@router.get("/", response_model=list[TrackListOut])
async def list_tracks(service: TrackService = Depends(get_track_service)):
    tracks = await service.get_tracks()
    return tracks
