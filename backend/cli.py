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
  # Convert single GPX file to video
  python cli.py input.gpx

  # Merge multiple files (GPX + TCX for GPS + heart rate)
  python cli.py route.gpx heartrate.tcx -o output.mp4

  # Specify data source priorities by file index (1-based)
  python cli.py file1.gpx file2.tcx --gps-source 1 --hr-source 2

  # Specify data source priorities by filename
  python cli.py route.gpx hr.tcx --gps-source route.gpx --hr-source hr.tcx

  # Custom video settings
  python cli.py input.tcx -o output.mp4 --width 1280 --height 720 --fps 60

  # Analyze multiple files before conversion
  python cli.py route.gpx heartrate.tcx -a

  # Supported file formats: .gpx, .tcx, .fit
        """
    )

    parser.add_argument(
        'inputs',
        type=str,
        nargs='+',
        help='Input activity file(s) (GPX/TCX/FIT). Multiple files will be merged by timestamp.'
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

    # Data source priority options
    parser.add_argument(
        '--gps-source',
        type=str,
        default=None,
        help='Priority file for GPS data (latitude/longitude). Specify filename or index (1, 2, ...). Default: auto-detect (prefer GPX)'
    )

    parser.add_argument(
        '--speed-source',
        type=str,
        default=None,
        help='Priority file for speed data. Specify filename or index (1, 2, ...). Default: auto-detect (prefer GPX)'
    )

    parser.add_argument(
        '--elevation-source',
        type=str,
        default=None,
        help='Priority file for elevation data. Specify filename or index (1, 2, ...). Default: auto-detect (prefer GPX)'
    )

    parser.add_argument(
        '--hr-source',
        type=str,
        default=None,
        help='Priority file for heart rate data. Specify filename or index (1, 2, ...). Default: auto-detect (prefer TCX)'
    )

    parser.add_argument(
        '--cadence-source',
        type=str,
        default=None,
        help='Priority file for cadence data. Specify filename or index (1, 2, ...). Default: first available'
    )

    parser.add_argument(
        '--power-source',
        type=str,
        default=None,
        help='Priority file for power data. Specify filename or index (1, 2, ...). Default: first available'
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


def merge_activity_data(activity_data_list, input_files, priority_sources=None, verbose: bool = False):
    """
    Merge multiple activity data by timestamp.

    Args:
        activity_data_list: List of parsed activity data
        input_files: List of input file paths
        priority_sources: Dict with priority settings {'gps': file_idx, 'hr': file_idx, ...}
        verbose: Enable verbose output

    Priority: GPX for GPS/speed/distance, TCX for heart_rate (default)
    Can be overridden with priority_sources parameter
    """
    if len(activity_data_list) == 1:
        return activity_data_list[0]

    if verbose:
        print(f"\nMerging {len(activity_data_list)} activity files...")
        if priority_sources:
            print("  Data source priorities:")
            for data_type, file_idx in priority_sources.items():
                if file_idx is not None:
                    print(f"    {data_type}: {os.path.basename(input_files[file_idx])}")

    # Collect all points with their timestamps
    all_points = []
    file_types = {}  # Track which file each point came from

    for idx, activity_data in enumerate(activity_data_list):
        for point in activity_data['points']:
            elapsed_time = point.get('elapsed_time', 0)
            all_points.append({
                'time': elapsed_time,
                'point': point,
                'file_idx': idx
            })

    # Sort by timestamp
    all_points.sort(key=lambda x: x['time'])

    # Group points by similar timestamps (within 1 second tolerance)
    merged_points = []
    time_tolerance = 1.0  # seconds

    # Default priority sources if not specified
    if priority_sources is None:
        priority_sources = {}

    i = 0
    while i < len(all_points):
        current_time = all_points[i]['time']
        group = [all_points[i]]

        # Find all points within tolerance
        j = i + 1
        while j < len(all_points) and all_points[j]['time'] - current_time <= time_tolerance:
            group.append(all_points[j])
            j += 1

        # Merge points in this time group
        merged_point = {}

        # Helper function to find point from specific source
        def find_point_from_source(data_type, field_names):
            """Find point with data from priority source"""
            priority_idx = priority_sources.get(data_type)

            # If priority source specified, use it
            if priority_idx is not None:
                for item in group:
                    if item['file_idx'] == priority_idx:
                        # Check if this point has the requested data
                        if any(item['point'].get(field) is not None for field in field_names):
                            return item['point']

            # Otherwise use first available
            for item in group:
                if any(item['point'].get(field) is not None for field in field_names):
                    return item['point']

            return None

        # Get priority points for different data types
        gps_point = find_point_from_source('gps', ['latitude', 'longitude'])
        speed_point = find_point_from_source('speed', ['speed'])
        elevation_point = find_point_from_source('elevation', ['elevation'])
        hr_point = find_point_from_source('hr', ['heart_rate'])
        cadence_point = find_point_from_source('cadence', ['cadence'])
        power_point = find_point_from_source('power', ['power'])

        # Merge all available data with priorities
        for item in group:
            point = item['point']
            for key, value in point.items():
                if key not in merged_point or value is not None:
                    # GPS data: prefer from gps_point
                    if key in ['latitude', 'longitude'] and gps_point:
                        merged_point[key] = gps_point[key]
                    # Speed: prefer from speed_point
                    elif key == 'speed' and speed_point:
                        merged_point[key] = speed_point.get(key)
                    # Elevation: prefer from elevation_point
                    elif key == 'elevation' and elevation_point:
                        merged_point[key] = elevation_point.get(key)
                    # Heart rate: prefer from hr_point
                    elif key == 'heart_rate' and hr_point:
                        merged_point[key] = hr_point.get(key)
                    # Cadence: prefer from cadence_point
                    elif key == 'cadence' and cadence_point:
                        merged_point[key] = cadence_point.get(key)
                    # Power: prefer from power_point
                    elif key == 'power' and power_point:
                        merged_point[key] = power_point.get(key)
                    # Other fields: use first non-null value
                    elif merged_point.get(key) is None:
                        merged_point[key] = value

        # Use average elapsed_time for the group
        merged_point['elapsed_time'] = sum(item['time'] for item in group) / len(group)

        merged_points.append(merged_point)
        i = j

    # Build merged activity_data
    # Use the first activity_data as template
    merged_data = activity_data_list[0].copy()
    merged_data['points'] = merged_points

    # Recalculate statistics
    if merged_points:
        # Distance and speed
        total_distance = sum(p.get('distance', 0) for p in merged_points)
        max_speed = max((p.get('speed', 0) for p in merged_points), default=0)
        speeds = [p.get('speed', 0) for p in merged_points if p.get('speed', 0) > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0

        # Elevation
        elevations = [p.get('elevation') for p in merged_points if p.get('elevation') is not None]
        max_elevation = max(elevations) if elevations else None
        min_elevation = min(elevations) if elevations else None

        # Calculate elevation gain/loss
        total_elevation_gain = 0
        total_elevation_loss = 0
        for i in range(1, len(merged_points)):
            prev_elev = merged_points[i-1].get('elevation')
            curr_elev = merged_points[i].get('elevation')
            if prev_elev is not None and curr_elev is not None:
                diff = curr_elev - prev_elev
                if diff > 0:
                    total_elevation_gain += diff
                else:
                    total_elevation_loss += abs(diff)

        # Duration
        total_duration = merged_points[-1].get('elapsed_time', 0)

        # Update merged data
        merged_data['total_distance'] = total_distance
        merged_data['total_duration'] = total_duration
        merged_data['max_speed'] = max_speed
        merged_data['avg_speed'] = avg_speed
        merged_data['max_elevation'] = max_elevation
        merged_data['min_elevation'] = min_elevation
        merged_data['total_elevation_gain'] = total_elevation_gain
        merged_data['total_elevation_loss'] = total_elevation_loss

    if verbose:
        print(f"✓ Merged into {len(merged_points)} points")
        print(f"  Duration: {merged_data['total_duration']:.2f} seconds")
        print(f"  Distance: {merged_data['total_distance']/1000:.2f} km")

    return merged_data


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


def resolve_source_index(source_spec, input_files):
    """
    Resolve source specification to file index.

    Args:
        source_spec: Either a filename or an index (1-based)
        input_files: List of input file paths

    Returns:
        File index (0-based) or None if not found
    """
    if source_spec is None:
        return None

    # Try to parse as integer index (1-based)
    try:
        idx = int(source_spec)
        if 1 <= idx <= len(input_files):
            return idx - 1  # Convert to 0-based
        else:
            print(f"Error: Index {idx} out of range. Valid range: 1-{len(input_files)}", file=sys.stderr)
            sys.exit(1)
    except ValueError:
        pass

    # Try to match as filename
    for idx, input_file in enumerate(input_files):
        if os.path.basename(input_file) == source_spec or input_file == source_spec:
            return idx

    # Not found
    print(f"Error: Source file not found: {source_spec}", file=sys.stderr)
    print(f"Available files:", file=sys.stderr)
    for idx, f in enumerate(input_files, 1):
        print(f"  {idx}: {f}", file=sys.stderr)
    sys.exit(1)


def main():
    """Main CLI entry point"""
    args = parse_args()

    # Check if input files exist
    for input_file in args.inputs:
        if not os.path.exists(input_file):
            print(f"Error: Input file not found: {input_file}", file=sys.stderr)
            sys.exit(1)

    # Detect file types
    file_types = []
    try:
        for input_file in args.inputs:
            file_type = detect_file_type(input_file)
            file_types.append(file_type)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Process priority source options
    priority_sources = {}
    if len(args.inputs) > 1:
        priority_sources['gps'] = resolve_source_index(args.gps_source, args.inputs)
        priority_sources['speed'] = resolve_source_index(args.speed_source, args.inputs)
        priority_sources['elevation'] = resolve_source_index(args.elevation_source, args.inputs)
        priority_sources['hr'] = resolve_source_index(args.hr_source, args.inputs)
        priority_sources['cadence'] = resolve_source_index(args.cadence_source, args.inputs)
        priority_sources['power'] = resolve_source_index(args.power_source, args.inputs)

    # Determine output path (skip if in analyze mode)
    output_path = None
    if not args.analyze:
        if args.output:
            output_path = args.output
        else:
            # Generate default output filename from first input file
            input_path = Path(args.inputs[0])
            if len(args.inputs) > 1:
                # Add "_merged" suffix for multiple files
                output_path = str(input_path.with_stem(f"{input_path.stem}_merged").with_suffix('.mp4'))
            else:
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

    # Parse activity files
    activity_data_list = []
    for input_file, file_type in zip(args.inputs, file_types):
        activity_data = parse_activity_file(input_file, file_type, args.verbose)
        activity_data_list.append(activity_data)

    # Merge activity data if multiple files
    if len(activity_data_list) > 1:
        activity_data = merge_activity_data(activity_data_list, args.inputs, priority_sources, args.verbose)
    else:
        activity_data = activity_data_list[0]

    # Check if --require-time flag is set
    if args.require_time and not activity_data.get('has_time_data', False):
        print(f"Error: File does not contain actual timestamp data.", file=sys.stderr)
        print(f"The file only has GPS coordinates without time information.", file=sys.stderr)
        print(f"Please use a file with recorded timestamps, or remove the --require-time flag.", file=sys.stderr)
        sys.exit(1)

    # Analyze mode - just show statistics and exit
    if args.analyze:
        if len(args.inputs) > 1:
            # Show individual files first
            for i, (input_file, data) in enumerate(zip(args.inputs, activity_data_list)):
                print(f"\n{'='*70}")
                print(f"File {i+1}/{len(args.inputs)}: {os.path.basename(input_file)}")
                print(f"{'='*70}")
                analyze_activity_data(data, input_file)
            # Then show merged data
            print(f"\n{'='*70}")
            print(f"MERGED DATA ({len(args.inputs)} files)")
            print(f"{'='*70}")
            analyze_activity_data(activity_data, "merged")
        else:
            analyze_activity_data(activity_data, args.inputs[0])
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
