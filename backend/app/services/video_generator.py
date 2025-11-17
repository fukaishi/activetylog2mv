import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips
import os
from typing import Dict, List, Callable, Optional


class VideoGenerator:
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

    def create_video(self, activity_data: Dict, output_path: str, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        Create a video from activity data

        Args:
            activity_data: Parsed activity data from GPX/TCX/FIT file
            output_path: Path to save the output video

        Returns:
            Path to the generated video file
        """
        points = activity_data['points']
        total_duration = activity_data['total_duration']

        if not points or total_duration == 0:
            raise ValueError("No valid activity data to generate video")

        # Calculate total frames needed
        total_frames = int(total_duration * self.fps)

        if progress_callback:
            progress_callback(0, total_frames, "Generating frames...")

        # Generate frames
        frames = []
        for frame_idx in range(total_frames):
            current_time = frame_idx / self.fps

            # Find the closest data point for this time
            point_data = self._get_point_at_time(points, current_time)

            # Create frame with overlay
            frame = self._create_frame(point_data, current_time, activity_data)
            frames.append(frame)

            # Report progress every 10 frames or at the end
            if progress_callback and (frame_idx % 10 == 0 or frame_idx == total_frames - 1):
                progress_callback(frame_idx + 1, total_frames, "Generating frames...")

        if progress_callback:
            progress_callback(total_frames, total_frames, "Creating video clips...")

        # Create video from frames using moviepy
        clips = []
        frame_duration = 1.0 / self.fps

        for i, frame in enumerate(frames):
            clip = ImageClip(frame).set_duration(frame_duration)
            clips.append(clip)

            if progress_callback and (i % 100 == 0 or i == len(frames) - 1):
                progress_callback(i + 1, len(frames), "Creating video clips...")

        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio=False,
            preset='medium',
            threads=4
        )

        return output_path

    def _get_point_at_time(self, points: List[Dict], current_time: float) -> Dict:
        """Find the data point closest to the current time"""
        for i, point in enumerate(points):
            if point['elapsed_time'] >= current_time:
                return point
        return points[-1]

    def _create_frame(self, point_data: Dict, current_time: float, activity_data: Dict) -> np.ndarray:
        """Create a single frame with activity data overlay"""
        # Create black background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Convert to PIL for better text rendering
        pil_image = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_image)

        # Try to load a font, fallback to default if not available
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Format time as HH:MM:SS
        hours = int(current_time // 3600)
        minutes = int((current_time % 3600) // 60)
        seconds = int(current_time % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Display data at different positions
        # Top: Elapsed Time
        draw.text((self.width // 2 - 150, 50), f"TIME: {time_str}", fill=(255, 255, 255), font=font_large)

        # Top Right: Speed
        speed = point_data.get('speed', 0)
        draw.text((self.width - 400, 50), f"SPEED", fill=(255, 200, 100), font=font_medium)
        draw.text((self.width - 400, 100), f"{speed:.1f} km/h", fill=(255, 255, 255), font=font_large)

        # Top Left: Distance
        total_distance = activity_data['total_distance'] / 1000  # Convert to km
        elapsed_distance = 0
        for point in activity_data['points']:
            if point['elapsed_time'] <= current_time:
                elapsed_distance += point.get('distance', 0)
            else:
                break
        elapsed_distance = elapsed_distance / 1000  # Convert to km

        draw.text((50, 50), f"DISTANCE", fill=(100, 200, 255), font=font_medium)
        draw.text((50, 100), f"{elapsed_distance:.2f} km", fill=(255, 255, 255), font=font_large)

        # Bottom Left: Elevation
        elevation = point_data.get('elevation', 0)
        if elevation is not None:
            draw.text((50, self.height - 150), f"ELEVATION", fill=(100, 255, 100), font=font_medium)
            draw.text((50, self.height - 100), f"{elevation:.1f} m", fill=(255, 255, 255), font=font_large)

        # Bottom Right: Heart Rate (if available)
        heart_rate = point_data.get('heart_rate')
        if heart_rate:
            draw.text((self.width - 400, self.height - 150), f"HEART RATE", fill=(255, 100, 100), font=font_medium)
            draw.text((self.width - 400, self.height - 100), f"{heart_rate} bpm", fill=(255, 255, 255), font=font_large)

        # Center: Current coordinates
        lat = point_data.get('latitude', 0)
        lon = point_data.get('longitude', 0)
        if lat and lon:
            coord_text = f"LAT: {lat:.6f}  LON: {lon:.6f}"
            draw.text((self.width // 2 - 300, self.height // 2), coord_text, fill=(200, 200, 200), font=font_small)

        # Bottom Center: Additional stats
        avg_speed = activity_data.get('avg_speed', 0)
        max_speed = activity_data.get('max_speed', 0)
        stats_text = f"AVG: {avg_speed:.1f} km/h  |  MAX: {max_speed:.1f} km/h"
        draw.text((self.width // 2 - 300, self.height - 80), stats_text, fill=(180, 180, 180), font=font_small)

        # Convert back to numpy array
        frame = np.array(pil_image)

        return frame
