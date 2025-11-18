from tcxparser import TCXParser as TCXParserLib
from typing import Dict
from datetime import datetime
from dateutil import parser as dateutil_parser


class TCXParser:
    @staticmethod
    def parse(file_path: str) -> Dict:
        """Parse TCX file and extract activity data"""
        tcx = TCXParserLib(file_path)

        activity_data = {
            'points': [],
            'total_duration': 0,
            'total_distance': 0,
            'max_speed': 0,
            'avg_speed': 0,
            'max_elevation': None,
            'min_elevation': None,
            'total_elevation_gain': 0,
            'total_elevation_loss': 0,
            'has_time_data': False,
        }

        # Get activity data
        activity_data['total_distance'] = tcx.distance if tcx.distance else 0
        activity_data['total_duration'] = tcx.duration if tcx.duration else 0
        if activity_data['total_duration'] > 0:
            activity_data['has_time_data'] = True

        # Get data arrays from TCX (these are methods, not properties)
        position_values = tcx.position_values() if tcx.position_values else []
        time_values = tcx.time_values() if tcx.time_values else []
        altitude_points = tcx.altitude_points() if tcx.altitude_points else []
        hr_values = tcx.hr_values() if tcx.hr_values else []
        cadence_values = tcx.cadence_values() if tcx.cadence_values else []
        distance_values = tcx.distance_values() if tcx.distance_values else []

        # Determine the number of points (use the longest array)
        num_points = max(
            len(position_values),
            len(time_values),
            len(altitude_points)
        )

        # Parse trackpoints
        start_time = None
        if tcx.started_at:
            start_time = dateutil_parser.parse(tcx.started_at) if isinstance(tcx.started_at, str) else tcx.started_at

        all_points = []

        for i in range(num_points):
            # Get position (latitude, longitude)
            lat, lon = None, None
            if i < len(position_values) and position_values[i]:
                lat, lon = position_values[i]

            # Get time
            point_time_str = time_values[i] if i < len(time_values) else None
            point_time = None
            if point_time_str:
                point_time = dateutil_parser.parse(point_time_str) if isinstance(point_time_str, str) else point_time_str

            elapsed_time = 0
            if point_time and start_time:
                elapsed_time = (point_time - start_time).total_seconds()

            # Get elevation
            elevation = altitude_points[i] if i < len(altitude_points) else None

            # Get heart rate
            heart_rate = hr_values[i] if i < len(hr_values) else None

            # Get cadence
            cadence = cadence_values[i] if i < len(cadence_values) else None

            point_data = {
                'latitude': lat,
                'longitude': lon,
                'elevation': elevation,
                'time': point_time.isoformat() if point_time else None,
                'elapsed_time': elapsed_time,
                'speed': 0,
                'distance': 0,
                'heart_rate': heart_rate,
                'cadence': cadence,
            }

            all_points.append(point_data)

        # Calculate speeds
        for i in range(1, len(all_points)):
            prev_point = all_points[i-1]
            curr_point = all_points[i]

            # Calculate distance
            from math import radians, cos, sin, asin, sqrt
            lat1, lon1 = prev_point['latitude'], prev_point['longitude']
            lat2, lon2 = curr_point['latitude'], curr_point['longitude']

            if lat1 and lon1 and lat2 and lon2:
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371000  # Radius of earth in meters
                distance = c * r

                curr_point['distance'] = distance

                # Calculate speed
                time_diff = curr_point['elapsed_time'] - prev_point['elapsed_time']
                if time_diff > 0:
                    speed = distance / time_diff  # m/s
                    curr_point['speed'] = speed * 3.6  # Convert to km/h
                    activity_data['max_speed'] = max(activity_data['max_speed'], curr_point['speed'])

        activity_data['points'] = all_points

        # If duration is still 0 (no time data), estimate it
        if activity_data['total_duration'] == 0 and all_points:
            if all_points[-1]['elapsed_time'] > 0:
                activity_data['total_duration'] = all_points[-1]['elapsed_time']
                activity_data['has_time_data'] = True
            elif activity_data['total_distance'] > 0:
                # Estimate duration: assume average speed of 15 km/h
                assumed_speed_ms = 15 / 3.6
                estimated_duration = activity_data['total_distance'] / assumed_speed_ms
                activity_data['total_duration'] = estimated_duration

                # Recalculate elapsed_time for each point
                cumulative_distance = 0
                for i, point in enumerate(all_points):
                    if i > 0:
                        cumulative_distance += point['distance']
                    point['elapsed_time'] = (cumulative_distance / activity_data['total_distance']) * estimated_duration if activity_data['total_distance'] > 0 else 0
            else:
                # Fallback: 1 second per point
                activity_data['total_duration'] = len(all_points)
                for i, point in enumerate(all_points):
                    point['elapsed_time'] = i

        if activity_data['total_duration'] > 0:
            activity_data['avg_speed'] = (activity_data['total_distance'] / activity_data['total_duration'] * 3.6)

        # Elevation data
        elevations = [p['elevation'] for p in all_points if p['elevation'] is not None]
        if elevations:
            activity_data['max_elevation'] = max(elevations)
            activity_data['min_elevation'] = min(elevations)

            # Calculate elevation gain/loss
            for i in range(1, len(all_points)):
                if all_points[i]['elevation'] and all_points[i-1]['elevation']:
                    diff = all_points[i]['elevation'] - all_points[i-1]['elevation']
                    if diff > 0:
                        activity_data['total_elevation_gain'] += diff
                    else:
                        activity_data['total_elevation_loss'] += abs(diff)

        return activity_data
