from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from typing import Optional
import os
import uuid
import shutil
from app.parsers.gpx_parser import GPXParser
from app.parsers.tcx_parser import TCXParser
from app.parsers.fit_parser import FITParser
from app.services.video_generator import VideoGenerator
from app.models.schemas import VideoGenerationResponse, VideoStatusResponse
from app.core.config import get_settings
from app.core.supabase_client import supabase

router = APIRouter()
settings = get_settings()

# Store video generation status (in production, use a database)
video_status = {}


async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """Verify Supabase JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1] if " " in authorization else authorization

        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.post("/upload", response_model=VideoGenerationResponse)
async def upload_activity_file(
    file: UploadFile = File(...),
    user: dict = Depends(verify_token)
):
    """
    Upload GPX/TCX/FIT file and generate video
    """
    # Validate file type
    allowed_extensions = ['.gpx', '.tcx', '.fit']
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Generate unique ID for this video
    video_id = str(uuid.uuid4())

    # Create upload directory if it doesn't exist
    upload_dir = settings.upload_dir
    output_dir = settings.output_dir
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Save uploaded file
    file_path = os.path.join(upload_dir, f"{video_id}{file_ext}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Initialize status
    video_status[video_id] = {
        'status': 'processing',
        'progress': 0.0,
        'error': None,
        'video_url': None
    }

    # Process file and generate video
    try:
        # Parse file based on type
        if file_ext == '.gpx':
            activity_data = GPXParser.parse(file_path)
        elif file_ext == '.tcx':
            activity_data = TCXParser.parse(file_path)
        elif file_ext == '.fit':
            activity_data = FITParser.parse(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        video_status[video_id]['progress'] = 0.3

        # Generate video
        output_path = os.path.join(output_dir, f"{video_id}.mp4")
        video_generator = VideoGenerator()

        video_status[video_id]['progress'] = 0.5

        video_generator.create_video(activity_data, output_path)

        video_status[video_id]['status'] = 'completed'
        video_status[video_id]['progress'] = 1.0
        video_status[video_id]['video_url'] = f"/api/videos/{video_id}"

        # Clean up uploaded file
        os.remove(file_path)

        return VideoGenerationResponse(
            video_id=video_id,
            status='completed',
            message='Video generated successfully',
            video_url=f"/api/videos/{video_id}"
        )

    except Exception as e:
        video_status[video_id]['status'] = 'failed'
        video_status[video_id]['error'] = str(e)

        # Clean up files
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")


@router.get("/videos/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: str, user: dict = Depends(verify_token)):
    """Get video generation status"""
    if video_id not in video_status:
        raise HTTPException(status_code=404, detail="Video not found")

    status = video_status[video_id]

    return VideoStatusResponse(
        video_id=video_id,
        status=status['status'],
        progress=status['progress'],
        video_url=status['video_url'],
        error=status['error']
    )


@router.get("/videos/{video_id}")
async def download_video(video_id: str, user: dict = Depends(verify_token)):
    """Download generated video"""
    video_path = os.path.join(settings.output_dir, f"{video_id}.mp4")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"activity_{video_id}.mp4"
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
