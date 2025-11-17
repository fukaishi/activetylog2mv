from pydantic import BaseModel
from typing import Optional


class VideoGenerationResponse(BaseModel):
    video_id: str
    status: str
    message: str
    video_url: Optional[str] = None


class VideoStatusResponse(BaseModel):
    video_id: str
    status: str
    progress: Optional[float] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
