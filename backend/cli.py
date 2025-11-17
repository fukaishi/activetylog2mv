#!/usr/bin/env python3
"""
CLI tool for converting activity files (GPX/TCX/FIT) to video
"""

import argparse
import os
import sys
from pathlib import Path

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


def generate_video(activity_data, output_path: str, width: int, height: int, fps: int, verbose: bool = False):
    """Generate video from activity data"""
    if verbose:
        print(f"\nGenerating video...")
        print(f"  Output: {output_path}")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps}")

    try:
        generator = VideoGenerator(width=width, height=height, fps=fps)
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

    # Determine output path
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

    # Generate video
    generate_video(activity_data, output_path, args.width, args.height, args.fps, args.verbose)

    if args.verbose:
        print("=" * 60)
        print("Done!")
        print("=" * 60)
    else:
        print(f"Video generated: {output_path}")


if __name__ == '__main__':
    main()
