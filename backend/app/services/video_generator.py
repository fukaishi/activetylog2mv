import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips
import os
from typing import Dict, List, Callable, Optional
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO


class VideoGenerator:
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30,
                 layout: str = 'corners', font_size: str = 'medium', items: str = None, show_map: bool = False,
                 show_elevation: bool = False, map_position: str = 'background', elevation_position: str = 'bottom'):
        self.width = width
        self.height = height
        self.fps = fps
        self.layout = layout
        self.font_size = font_size
        self.show_map = show_map
        self.show_elevation = show_elevation
        self.map_position = map_position
        self.elevation_position = elevation_position

        # Parse items configuration
        self.display_items = self._parse_items(items)

        # Font size mapping
        self.font_sizes = {
            'small': 30,
            'medium': 45,
            'large': 60
        }

    def _parse_items(self, items_str: str) -> Dict:
        """Parse items string into position-item mapping
        Format: "1:speed,2:distance,3:elevation,4:heart_rate"
        """
        if not items_str:
            # Default items based on layout
            return {
                1: 'distance',
                2: 'speed',
                3: 'elevation',
                4: 'heart_rate'
            }

        items_map = {}
        for item_def in items_str.split(','):
            item_def = item_def.strip()
            if ':' in item_def:
                pos, name = item_def.split(':', 1)
                items_map[int(pos)] = name.strip()

        return items_map

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

    def _generate_map(self, activity_data: Dict, current_point: Dict) -> Image:
        """Generate a simple route visualization with line and current position marker (no map tiles)"""
        # Create blank canvas
        canvas = Image.new('RGB', (self.width, self.height), color=(20, 20, 20))
        draw = ImageDraw.Draw(canvas)

        # Extract all GPS coordinates
        coords = []
        for point in activity_data['points']:
            lat = point.get('latitude')
            lon = point.get('longitude')
            if lat is not None and lon is not None:
                coords.append((lat, lon))

        if len(coords) < 2:
            return canvas

        # Find bounds
        lats = [c[0] for c in coords]
        lons = [c[1] for c in coords]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Add padding (10%)
        lat_range = max_lat - min_lat if max_lat != min_lat else 0.01
        lon_range = max_lon - min_lon if max_lon != min_lon else 0.01
        padding = 0.1
        min_lat -= lat_range * padding
        max_lat += lat_range * padding
        min_lon -= lon_range * padding
        max_lon += lon_range * padding

        # Convert GPS coordinates to pixel coordinates
        def gps_to_pixel(lat, lon):
            x = int((lon - min_lon) / (max_lon - min_lon) * (self.width - 100) + 50)
            y = int((max_lat - lat) / (max_lat - min_lat) * (self.height - 100) + 50)
            return (x, y)

        # Draw route line (up to current point)
        route_pixels = []
        for point in activity_data['points']:
            lat = point.get('latitude')
            lon = point.get('longitude')
            if lat is not None and lon is not None:
                route_pixels.append(gps_to_pixel(lat, lon))
                # Stop at current point
                if point['elapsed_time'] >= current_point['elapsed_time']:
                    break

        # Draw the route line
        if len(route_pixels) > 1:
            draw.line(route_pixels, fill='#0066FF', width=4)

        # Draw current position marker
        current_lat = current_point.get('latitude')
        current_lon = current_point.get('longitude')
        if current_lat is not None and current_lon is not None:
            current_pixel = gps_to_pixel(current_lat, current_lon)
            marker_size = 12
            draw.ellipse(
                [current_pixel[0] - marker_size, current_pixel[1] - marker_size,
                 current_pixel[0] + marker_size, current_pixel[1] + marker_size],
                fill='#FF0000',
                outline='#FFFFFF',
                width=2
            )

        return canvas

    def _generate_elevation_graph(self, activity_data: Dict, current_point: Dict, graph_width: int = 1920, graph_height: int = 250) -> Image:
        """Generate elevation profile graph with current position marker"""
        # Extract distance and elevation data
        distances = []
        elevations = []
        cumulative_distance = 0

        for point in activity_data['points']:
            cumulative_distance += point.get('distance', 0) / 1000  # Convert to km
            elevation = point.get('elevation')
            if elevation is not None:
                distances.append(cumulative_distance)
                elevations.append(elevation)

        if not distances or not elevations:
            # No elevation data, return blank graph
            return Image.new('RGB', (graph_width, graph_height), color=(0, 0, 0))

        # Find current position distance
        current_distance = 0
        for point in activity_data['points']:
            if point['elapsed_time'] > current_point['elapsed_time']:
                break
            current_distance += point.get('distance', 0) / 1000

        # Set Japanese font
        import matplotlib.font_manager as fm
        japanese_fonts = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
            "/usr/share/fonts/truetype/ipa-gothic/ipagp.ttf"
        ]

        font_prop = None
        for font_path in japanese_fonts:
            if os.path.exists(font_path):
                font_prop = fm.FontProperties(fname=font_path)
                break

        # If no Japanese font found, use default
        if not font_prop:
            font_prop = fm.FontProperties()

        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(graph_width/100, graph_height/100), dpi=100)
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#2a2a2a')

        # Plot elevation profile
        ax.fill_between(distances, elevations, color='#4CAF50', alpha=0.3)
        ax.plot(distances, elevations, color='#4CAF50', linewidth=2)

        # Mark current position
        if current_distance <= max(distances):
            # Find closest elevation for current distance
            current_elevation = elevations[0]
            for i, d in enumerate(distances):
                if d >= current_distance:
                    current_elevation = elevations[i]
                    break

            ax.plot(current_distance, current_elevation, 'ro', markersize=10, zorder=5)

        # Styling with Japanese font
        ax.set_xlabel('距離 (km)', color='white', fontsize=12, fontproperties=font_prop)
        ax.set_ylabel('標高 (m)', color='white', fontsize=12, fontproperties=font_prop)
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Convert plot to PIL Image
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        graph_image = Image.open(buf)

        return graph_image

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

    def _draw_text_with_background(self, draw: ImageDraw.Draw, position: tuple, text: str, font, text_color: tuple, bg_color: tuple, padding: int = 20, radius: int = 15, fixed_width: int = None):
        """Draw text with rounded background"""
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Use fixed width if specified, otherwise use text width
        box_width = fixed_width if fixed_width else text_width

        x, y = position
        # Draw rounded rectangle background
        self._draw_rounded_rectangle(
            draw,
            (x - padding, y - padding, x + box_width + padding, y + text_height + padding),
            radius,
            fill=bg_color
        )
        # Draw text
        draw.text((x, y), text, fill=text_color, font=font)

    def _calculate_fixed_box_width(self, font):
        """Calculate fixed box width based on longest expected text"""
        # Use "ケイデンス: 100 rpm" as reference for width
        sample_texts = [
            "ケイデンス: 100 rpm",
            "心拍数: 180 bpm",
            "距離: 99.99 km",
            "速度: 99.9 km/h",
            "標高: 9999.9 m"
        ]

        max_width = 0
        for text in sample_texts:
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            max_width = max(max_width, text_width)

        return max_width

    def _display_corners_layout(self, draw: ImageDraw.Draw, items: List, font):
        """Display items in four corners (top-left, top-right, bottom-left, bottom-right)"""
        # Calculate fixed width for consistent box sizes
        fixed_width = self._calculate_fixed_box_width(font)

        positions = [
            (50, 50),                           # Position 1: Top-left
            (self.width - fixed_width - 90, 50),             # Position 2: Top-right
            (50, self.height - 120),            # Position 3: Bottom-left
            (self.width - fixed_width - 90, self.height - 120)  # Position 4: Bottom-right
        ]

        for i, (pos, text, bg_color) in enumerate(items):
            if i < len(positions):
                self._draw_text_with_background(
                    draw,
                    positions[i],
                    text,
                    font,
                    (255, 255, 255),
                    bg_color,
                    padding=20,
                    radius=15,
                    fixed_width=fixed_width
                )

    def _display_bottom_right_layout(self, draw: ImageDraw.Draw, items: List, font):
        """Display all items stacked in bottom-right corner within a single rounded box"""
        if not items:
            return

        padding = 20
        line_spacing = 10

        # Use fixed width for consistent box size
        fixed_width = self._calculate_fixed_box_width(font)

        # Calculate total height needed
        total_height = 0
        text_heights = []

        for pos, text, bg_color in items:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_height = bbox[3] - bbox[1]
            text_heights.append(text_height)
            total_height += text_height

        # Add spacing between lines
        total_height += line_spacing * (len(items) - 1)

        # Calculate box position (bottom-right corner)
        box_width = fixed_width + padding * 2
        box_height = total_height + padding * 2
        box_x = self.width - box_width - 50
        box_y = self.height - box_height - 50

        # Draw single rounded rectangle background
        self._draw_rounded_rectangle(
            draw,
            (box_x, box_y, box_x + box_width, box_y + box_height),
            radius=15,
            fill=(40, 40, 40, 200)
        )

        # Draw each text item inside the box
        current_y = box_y + padding
        for i, (pos, text, bg_color) in enumerate(items):
            text_x = box_x + padding
            draw.text((text_x, current_y), text, fill=(255, 255, 255), font=font)
            current_y += text_heights[i] + line_spacing

    def _display_top_layout(self, draw: ImageDraw.Draw, items: List, font):
        """Display all items horizontally at the top"""
        num_items = len(items)
        if num_items == 0:
            return

        # Calculate fixed width for consistent box sizes
        fixed_width = self._calculate_fixed_box_width(font)

        # Calculate spacing based on fixed width
        total_width = self.width - 100
        spacing = total_width // num_items
        y = 50

        for i, (pos, text, bg_color) in enumerate(items):
            x = 50 + (i * spacing)
            self._draw_text_with_background(
                draw,
                (x, y),
                text,
                font,
                (255, 255, 255),
                bg_color,
                padding=20,
                radius=15,
                fixed_width=fixed_width
            )

    def _display_bottom_layout(self, draw: ImageDraw.Draw, items: List, font):
        """Display all items horizontally at the bottom"""
        num_items = len(items)
        if num_items == 0:
            return

        # Calculate fixed width for consistent box sizes
        fixed_width = self._calculate_fixed_box_width(font)

        # Calculate spacing based on fixed width
        total_width = self.width - 100
        spacing = total_width // num_items
        y = self.height - 120

        for i, (pos, text, bg_color) in enumerate(items):
            x = 50 + (i * spacing)
            self._draw_text_with_background(
                draw,
                (x, y),
                text,
                font,
                (255, 255, 255),
                bg_color,
                padding=20,
                radius=15,
                fixed_width=fixed_width
            )

    def _create_frame(self, point_data: Dict, current_time: float, activity_data: Dict) -> np.ndarray:
        """Create a single frame with activity data overlay"""
        # Create background
        if self.show_map and self.map_position == 'background':
            # Generate map as background
            pil_image = self._generate_map(activity_data, point_data)
            pil_image = pil_image.resize((self.width, self.height))
        else:
            # Create black background
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            pil_image = Image.fromarray(frame)

        draw = ImageDraw.Draw(pil_image)

        # Load font with specified size
        font_size_px = self.font_sizes.get(self.font_size, 45)

        try:
            # Try Japanese fonts first
            font_paths = [
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ]

            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size_px)
                    break
                except:
                    continue

            if not font:
                raise Exception("No font found")
        except:
            font = ImageFont.load_default()

        # Calculate distance
        total_distance = activity_data['total_distance'] / 1000  # Convert to km
        elapsed_distance = 0
        for point in activity_data['points']:
            if point['elapsed_time'] <= current_time:
                elapsed_distance += point.get('distance', 0)
            else:
                break
        elapsed_distance = elapsed_distance / 1000  # Convert to km

        # Get current values
        speed = point_data.get('speed', 0)
        elevation = point_data.get('elevation', 0)
        heart_rate = point_data.get('heart_rate')

        # Build item data
        item_values = {
            'speed': (f"速度: {speed:.1f} km/h", (60, 50, 30, 200)),
            'distance': (f"距離: {elapsed_distance:.2f} km", (30, 50, 60, 200)),
            'elevation': (f"標高: {elevation:.1f} m", (30, 60, 30, 200)) if elevation is not None else None,
            'heart_rate': (f"心拍数: {heart_rate} bpm", (60, 30, 30, 200)) if heart_rate else None
        }

        # Filter items to display based on configuration
        items_to_display = []
        for pos in sorted(self.display_items.keys()):
            item_name = self.display_items[pos]
            if item_name in item_values and item_values[item_name] is not None:
                items_to_display.append((pos, item_values[item_name][0], item_values[item_name][1]))

        # Display items based on layout
        if self.layout == 'corners':
            self._display_corners_layout(draw, items_to_display, font)
        elif self.layout == 'bottom-right':
            self._display_bottom_right_layout(draw, items_to_display, font)
        elif self.layout == 'top':
            self._display_top_layout(draw, items_to_display, font)
        elif self.layout == 'bottom':
            self._display_bottom_layout(draw, items_to_display, font)

        # Add map if not background
        if self.show_map and self.map_position != 'background':
            map_width, map_height = 600, 400  # Small map size
            map_image = self._generate_map(activity_data, point_data)
            map_image = map_image.resize((map_width, map_height))

            # Calculate position based on map_position
            if self.map_position == 'top-left':
                map_x, map_y = 20, 20
            elif self.map_position == 'top-right':
                map_x, map_y = self.width - map_width - 20, 20
            elif self.map_position == 'bottom-left':
                map_x, map_y = 20, self.height - map_height - 20
            elif self.map_position == 'bottom-right':
                map_x, map_y = self.width - map_width - 20, self.height - map_height - 20

            pil_image.paste(map_image, (map_x, map_y))

        # Add elevation graph if enabled
        if self.show_elevation:
            # Determine graph size and position based on elevation_position
            if self.elevation_position in ['bottom', 'top']:
                # Full width
                graph_width, graph_height = self.width, 250
            elif self.elevation_position == 'bottom-center':
                # Center width (60%)
                graph_width, graph_height = int(self.width * 0.6), 250
            else:
                # Corner positions (40% width)
                graph_width, graph_height = int(self.width * 0.4), 200

            elevation_graph = self._generate_elevation_graph(activity_data, point_data, graph_width, graph_height)

            # Calculate position
            if self.elevation_position == 'bottom':
                graph_x, graph_y = 0, self.height - graph_height
            elif self.elevation_position == 'top':
                graph_x, graph_y = 0, 0
            elif self.elevation_position == 'bottom-center':
                graph_x, graph_y = (self.width - graph_width) // 2, self.height - graph_height
            elif self.elevation_position == 'bottom-left':
                graph_x, graph_y = 20, self.height - graph_height - 20
            elif self.elevation_position == 'bottom-right':
                graph_x, graph_y = self.width - graph_width - 20, self.height - graph_height - 20

            pil_image.paste(elevation_graph, (graph_x, graph_y))

        # Convert back to numpy array
        frame = np.array(pil_image)

        return frame
