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

    def _draw_rounded_rectangle(self, draw: ImageDraw.Draw, xy: tuple, radius: int, fill: tuple, outline: tuple = None, width: int = 0):
        """Draw a rounded rectangle"""
        x1, y1, x2, y2 = xy
        # Draw main rectangle
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
        # Draw corners
        draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill, outline=outline, width=width)
        draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill, outline=outline, width=width)
        draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill, outline=outline, width=width)
        draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill, outline=outline, width=width)

    def _draw_text_with_background(self, draw: ImageDraw.Draw, position: tuple, text: str, font, text_color: tuple, bg_color: tuple, padding: int = 20, radius: int = 15):
        """Draw text with rounded background"""
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x, y = position
        # Draw rounded rectangle background
        self._draw_rounded_rectangle(
            draw,
            (x - padding, y - padding, x + text_width + padding, y + text_height + padding),
            radius,
            fill=bg_color
        )
        # Draw text
        draw.text((x, y), text, fill=text_color, font=font)

    def _create_frame(self, point_data: Dict, current_time: float, activity_data: Dict) -> np.ndarray:
        """Create a single frame with activity data overlay"""
        # Create black background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Convert to PIL for better text rendering
        pil_image = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_image)

        # Try to load Japanese font, fallback to default if not available
        try:
            # Try Japanese fonts first
            font_paths = [
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ]

            font_large = None
            for font_path in font_paths:
                try:
                    font_large = ImageFont.truetype(font_path, 100)
                    font_medium = ImageFont.truetype(font_path, 60)
                    font_small = ImageFont.truetype(font_path, 45)
                    break
                except:
                    continue

            if not font_large:
                raise Exception("No font found")
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Format time as HH:MM:SS
        hours = int(current_time // 3600)
        minutes = int((current_time % 3600) // 60)
        seconds = int(current_time % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Display data at different positions with rounded backgrounds
        # Top Center: Elapsed Time
        self._draw_text_with_background(
            draw,
            (self.width // 2 - 200, 50),
            f"経過時間: {time_str}",
            font_large,
            (255, 255, 255),
            (50, 50, 50, 200),
            padding=30,
            radius=20
        )

        # Top Right: Speed
        speed = point_data.get('speed', 0)
        self._draw_text_with_background(
            draw,
            (self.width - 550, 50),
            f"速度",
            font_medium,
            (255, 200, 100),
            (40, 40, 40, 200),
            padding=25,
            radius=15
        )
        self._draw_text_with_background(
            draw,
            (self.width - 550, 140),
            f"{speed:.1f} km/h",
            font_large,
            (255, 255, 255),
            (60, 50, 30, 200),
            padding=30,
            radius=20
        )

        # Top Left: Distance
        total_distance = activity_data['total_distance'] / 1000  # Convert to km
        elapsed_distance = 0
        for point in activity_data['points']:
            if point['elapsed_time'] <= current_time:
                elapsed_distance += point.get('distance', 0)
            else:
                break
        elapsed_distance = elapsed_distance / 1000  # Convert to km

        self._draw_text_with_background(
            draw,
            (50, 50),
            f"距離",
            font_medium,
            (100, 200, 255),
            (40, 40, 40, 200),
            padding=25,
            radius=15
        )
        self._draw_text_with_background(
            draw,
            (50, 140),
            f"{elapsed_distance:.2f} km",
            font_large,
            (255, 255, 255),
            (30, 50, 60, 200),
            padding=30,
            radius=20
        )

        # Bottom Left: Elevation
        elevation = point_data.get('elevation', 0)
        if elevation is not None:
            self._draw_text_with_background(
                draw,
                (50, self.height - 280),
                f"標高",
                font_medium,
                (100, 255, 100),
                (40, 40, 40, 200),
                padding=25,
                radius=15
            )
            self._draw_text_with_background(
                draw,
                (50, self.height - 190),
                f"{elevation:.1f} m",
                font_large,
                (255, 255, 255),
                (30, 60, 30, 200),
                padding=30,
                radius=20
            )

        # Bottom Right: Heart Rate (if available)
        heart_rate = point_data.get('heart_rate')
        if heart_rate:
            self._draw_text_with_background(
                draw,
                (self.width - 550, self.height - 280),
                f"心拍数",
                font_medium,
                (255, 100, 100),
                (40, 40, 40, 200),
                padding=25,
                radius=15
            )
            self._draw_text_with_background(
                draw,
                (self.width - 550, self.height - 190),
                f"{heart_rate} bpm",
                font_large,
                (255, 255, 255),
                (60, 30, 30, 200),
                padding=30,
                radius=20
            )

        # Center: Current coordinates
        lat = point_data.get('latitude', 0)
        lon = point_data.get('longitude', 0)
        if lat and lon:
            coord_text = f"位置: {lat:.6f}, {lon:.6f}"
            self._draw_text_with_background(
                draw,
                (self.width // 2 - 400, self.height // 2),
                coord_text,
                font_small,
                (200, 200, 200),
                (30, 30, 30, 180),
                padding=20,
                radius=12
            )

        # Bottom Center: Additional stats
        avg_speed = activity_data.get('avg_speed', 0)
        max_speed = activity_data.get('max_speed', 0)
        stats_text = f"平均: {avg_speed:.1f} km/h  |  最高: {max_speed:.1f} km/h"
        self._draw_text_with_background(
            draw,
            (self.width // 2 - 400, self.height - 100),
            stats_text,
            font_small,
            (180, 180, 180),
            (35, 35, 35, 180),
            padding=20,
            radius=12
        )

        # Convert back to numpy array
        frame = np.array(pil_image)

        return frame
