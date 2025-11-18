#!/usr/bin/env python3
"""
CLI tool for converting activity files (GPX/TCX/FIT) to video
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

from app.parsers.gpx_parser import GPXParser
from app.parsers.tcx_parser import TCXParser
from app.parsers.fit_parser import FITParser
from app.services.video_generator import VideoGenerator


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Convert activity files (GPX/TCX/FIT) to video',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert GPX file to video
  python cli.py input.gpx

  # Specify output file
  python cli.py input.gpx -o output.mp4

  # Custom video settings
  python cli.py input.tcx -o output.mp4 --width 1280 --height 720 --fps 60

  # Supported file formats: .gpx, .tcx, .fit
        """
    )

    parser.add_argument(
        'input',
        type=str,
        help='Input activity file (GPX/TCX/FIT)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output video file path (default: <input_filename>.mp4)'
    )

    parser.add_argument(
        '--width',
        type=int,
        default=1920,
        help='Video width in pixels (default: 1920)'
    )

    parser.add_argument(
        '--height',
        type=int,
        default=1080,
        help='Video height in pixels (default: 1080)'
    )

    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Video frame rate (default: 30)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '-a', '--analyze',
        action='store_true',
        help='Analyze mode: show file statistics without generating video'
    )

    parser.add_argument(
        '--require-time',
        action='store_true',
        help='Require actual timestamp data in file (reject estimated time)'
    )

    parser.add_argument(
        '--layout',
        type=str,
        choices=['corners', 'bottom-right', 'top', 'bottom'],
        default='corners',
        help='Display layout: corners (四方), bottom-right (右下), top (上部), bottom (下部) (default: corners)'
    )

    parser.add_argument(
        '--font-size',
        type=str,
        choices=['small', 'medium', 'large'],
        default='medium',
        help='Font size: small (30px), medium (45px), large (60px) (default: medium)'
    )

    parser.add_argument(
        '--items',
        type=str,
        default=None,
        help='Display items in format "1:speed,2:distance,3:elevation,4:heart_rate" (位置番号:項目名)'
    )

    parser.add_argument(
        '--show-map',
        action='store_true',
        help='Show map with current location and route (requires GPS data)'
    )

    parser.add_argument(
        '--map-position',
        type=str,
        choices=['background', 'top-left', 'top-right', 'bottom-left', 'bottom-right'],
        default='background',
        help='Map position: background (全体), top-left (左上), top-right (右上), bottom-left (左下), bottom-right (右下) (default: background)'
    )

    parser.add_argument(
        '--show-elevation',
        action='store_true',
        help='Show elevation profile graph'
    )

    parser.add_argument(
        '--elevation-position',
        type=str,
        choices=['bottom', 'top', 'bottom-left', 'bottom-right', 'bottom-center'],
        default='bottom',
        help='Elevation graph position: bottom (下部全幅), top (上部全幅), bottom-left (左下), bottom-right (右下), bottom-center (下中央) (default: bottom)'
    )

    return parser.parse_args()


def detect_file_type(file_path: str) -> str:
    """Detect file type from extension"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.gpx', '.tcx', '.fit']:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: .gpx, .tcx, .fit")
    return ext


def parse_activity_file(file_path: str, file_type: str, verbose: bool = False):
    """Parse activity file based on type"""
    if verbose:
        print(f"Parsing {file_type} file: {file_path}")

    try:
        if file_type == '.gpx':
            activity_data = GPXParser.parse(file_path)
        elif file_type == '.tcx':
            activity_data = TCXParser.parse(file_path)
        elif file_type == '.fit':
            activity_data = FITParser.parse(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Validate parsed data
        if not activity_data['points']:
            print(f"Error: No GPS points found in the file", file=sys.stderr)
            print(f"The file may be empty or contain only waypoints/routes without trackpoints", file=sys.stderr)
            sys.exit(1)

        if activity_data['total_duration'] == 0:
            print(f"Warning: No time data found in file. Duration will be estimated based on distance.", file=sys.stderr)

        # Check if time data is required
        if not activity_data.get('has_time_data', False):
            if verbose or not activity_data.get('has_time_data', False):
                print(f"Warning: File does not contain actual timestamp data. Time will be estimated.", file=sys.stderr)

        if verbose:
            print(f"✓ Parsed successfully")
            print(f"  Points: {len(activity_data['points'])}")
            print(f"  Duration: {activity_data['total_duration']:.2f} seconds ({activity_data['total_duration']/60:.2f} minutes)")
            print(f"  Distance: {activity_data['total_distance']/1000:.2f} km")
            print(f"  Max Speed: {activity_data['max_speed']:.2f} km/h")
            if activity_data['avg_speed'] > 0:
                print(f"  Avg Speed: {activity_data['avg_speed']:.2f} km/h")

        return activity_data

    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        import traceback
        if verbose:
            traceback.print_exc()
        sys.exit(1)


def print_progress(current: int, total: int, stage: str):
    """Print progress bar"""
    percent = (current / total) * 100 if total > 0 else 0
    bar_length = 40
    filled_length = int(bar_length * current // total) if total > 0 else 0
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r{stage} [{bar}] {percent:.1f}% ({current}/{total})', end='', flush=True)
    if current >= total:
        print()  # New line when complete


def analyze_activity_data(activity_data: Dict, file_path: str):
    """Display detailed analysis of activity data"""
    print("=" * 70)
    print(f"Activity File Analysis: {os.path.basename(file_path)}")
    print("=" * 70)

    # Basic info
    print(f"\n📊 Basic Information:")
    print(f"  Total Points: {len(activity_data['points'])}")
    print(f"  Has Timestamp Data: {'Yes' if activity_data.get('has_time_data', False) else 'No (estimated)'}")

    # Time info
    duration = activity_data['total_duration']
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    print(f"\n⏱️  Time Information:")
    print(f"  Total Duration: {hours:02d}:{minutes:02d}:{seconds:02d} ({duration:.2f} seconds)")

    # Distance info
    distance_km = activity_data['total_distance'] / 1000
    print(f"\n📏 Distance Information:")
    print(f"  Total Distance: {distance_km:.2f} km ({activity_data['total_distance']:.2f} m)")

    # Speed info
    print(f"\n⚡ Speed Information:")
    print(f"  Average Speed: {activity_data['avg_speed']:.2f} km/h")
    print(f"  Maximum Speed: {activity_data['max_speed']:.2f} km/h")

    # Elevation info
    if activity_data['max_elevation'] is not None:
        print(f"\n🏔️  Elevation Information:")
        print(f"  Maximum Elevation: {activity_data['max_elevation']:.2f} m")
        print(f"  Minimum Elevation: {activity_data['min_elevation']:.2f} m")
        print(f"  Total Elevation Gain: {activity_data['total_elevation_gain']:.2f} m")
        print(f"  Total Elevation Loss: {activity_data['total_elevation_loss']:.2f} m")

    # Check for additional data fields
    first_point = activity_data['points'][0] if activity_data['points'] else {}
    available_fields = []
    if first_point.get('heart_rate'):
        available_fields.append('Heart Rate')
    if first_point.get('cadence'):
        available_fields.append('Cadence')
    if first_point.get('power'):
        available_fields.append('Power')

    if available_fields:
        print(f"\n📈 Additional Data Fields:")
        for field in available_fields:
            print(f"  - {field}")

    # Sample data points
    print(f"\n📍 Sample Data Points (first 5):")
    for i, point in enumerate(activity_data['points'][:5]):
        print(f"  Point {i+1}:")
        print(f"    Time: {point.get('elapsed_time', 0):.2f}s")
        lat = point.get('latitude')
        lon = point.get('longitude')
        if lat is not None and lon is not None:
            print(f"    Location: {lat:.6f}, {lon:.6f}")
        else:
            print(f"    Location: N/A (no GPS data)")
        if point.get('elevation') is not None:
            print(f"    Elevation: {point['elevation']:.2f}m")
        if point.get('speed'):
            print(f"    Speed: {point['speed']:.2f} km/h")
        if point.get('heart_rate'):
            print(f"    Heart Rate: {point['heart_rate']} bpm")

    print("=" * 70)


def generate_video(activity_data, output_path: str, width: int, height: int, fps: int, verbose: bool = False,
                   layout: str = 'corners', font_size: str = 'medium', items: str = None, show_map: bool = False,
                   show_elevation: bool = False, map_position: str = 'background', elevation_position: str = 'bottom'):
    """Generate video from activity data"""
    if verbose:
        print(f"\nGenerating video...")
        print(f"  Output: {output_path}")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps}")
        print(f"  Layout: {layout}")
        print(f"  Font size: {font_size}")
        if items:
            print(f"  Items: {items}")
        print(f"  Show map: {show_map}")
        if show_map:
            print(f"  Map position: {map_position}")
        print(f"  Show elevation: {show_elevation}")
        if show_elevation:
            print(f"  Elevation position: {elevation_position}")

    try:
        generator = VideoGenerator(width=width, height=height, fps=fps,
                                  layout=layout, font_size=font_size, items=items, show_map=show_map,
                                  show_elevation=show_elevation, map_position=map_position,
                                  elevation_position=elevation_position)

        # Use progress callback if not verbose
        if not verbose:
            generator.create_video(activity_data, output_path, progress_callback=print_progress)
        else:
            generator.create_video(activity_data, output_path)

        if verbose:
            print(f"✓ Video generated successfully: {output_path}")

        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)

        if verbose:
            print(f"  File size: {file_size_mb:.2f} MB")

    except Exception as e:
        print(f"Error generating video: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    args = parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Detect file type
    try:
        file_type = detect_file_type(args.input)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine output path (skip if in analyze mode)
    output_path = None
    if not args.analyze:
        if args.output:
            output_path = args.output
        else:
            # Generate default output filename
            input_path = Path(args.input)
            output_path = str(input_path.with_suffix('.mp4'))

        # Check if output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            print(f"Error: Output directory does not exist: {output_dir}", file=sys.stderr)
            sys.exit(1)

        # Check if output file already exists
        if os.path.exists(output_path):
            response = input(f"Output file already exists: {output_path}. Overwrite? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Aborted.")
                sys.exit(0)

    if args.verbose:
        print("=" * 60)
        print("Activity Video Generator")
        print("=" * 60)

    # Parse activity file
    activity_data = parse_activity_file(args.input, file_type, args.verbose)

    # Check if --require-time flag is set
    if args.require_time and not activity_data.get('has_time_data', False):
        print(f"Error: File does not contain actual timestamp data.", file=sys.stderr)
        print(f"The file only has GPS coordinates without time information.", file=sys.stderr)
        print(f"Please use a file with recorded timestamps, or remove the --require-time flag.", file=sys.stderr)
        sys.exit(1)

    # Analyze mode - just show statistics and exit
    if args.analyze:
        analyze_activity_data(activity_data, args.input)
        sys.exit(0)

    # Check if GPS coordinates exist (required for video generation)
    has_gps_data = any(
        point.get('latitude') is not None and point.get('longitude') is not None
        for point in activity_data['points']
    )
    if not has_gps_data:
        print(f"Error: File does not contain GPS coordinates.", file=sys.stderr)
        print(f"This appears to be an indoor activity without location data.", file=sys.stderr)
        print(f"Video generation requires GPS coordinates to display the route and location.", file=sys.stderr)
        print(f"Tip: Use the --analyze (-a) flag to view the available data in this file.", file=sys.stderr)
        sys.exit(1)

    # Generate video
    generate_video(activity_data, output_path, args.width, args.height, args.fps, args.verbose,
                  args.layout, args.font_size, args.items, args.show_map, args.show_elevation,
                  args.map_position, args.elevation_position)

    if args.verbose:
        print("=" * 60)
        print("Done!")
        print("=" * 60)
    else:
        print(f"\nVideo generated: {output_path}")


if __name__ == '__main__':
    main()
