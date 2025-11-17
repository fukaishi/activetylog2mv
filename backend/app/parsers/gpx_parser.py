import gpxpy
from datetime import datetime
from typing import List, Dict, Optional


class GPXParser:
    @staticmethod
    def parse(file_path: str) -> Dict:
        """Parse GPX file and extract activity data"""
        with open(file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

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
        }

        all_points = []
        start_time = None

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if start_time is None:
                        start_time = point.time

                    elapsed_time = 0
                    if point.time and start_time:
                        elapsed_time = (point.time - start_time).total_seconds()

                    point_data = {
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation,
                        'time': point.time.isoformat() if point.time else None,
                        'elapsed_time': elapsed_time,
                        'speed': 0,
                        'distance': 0,
                    }

                    all_points.append(point_data)

        # Calculate speeds and distances
        for i in range(1, len(all_points)):
            prev_point = all_points[i-1]
            curr_point = all_points[i]

            # Calculate distance (simplified, using gpxpy's distance calculation would be better)
            lat1, lon1 = prev_point['latitude'], prev_point['longitude']
            lat2, lon2 = curr_point['latitude'], curr_point['longitude']

            # Haversine formula for distance
            from math import radians, cos, sin, asin, sqrt
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000  # Radius of earth in meters
            distance = c * r

            curr_point['distance'] = distance
            activity_data['total_distance'] += distance

            # Calculate speed
            time_diff = curr_point['elapsed_time'] - prev_point['elapsed_time']
            if time_diff > 0:
                speed = distance / time_diff  # m/s
                curr_point['speed'] = speed * 3.6  # Convert to km/h
                activity_data['max_speed'] = max(activity_data['max_speed'], curr_point['speed'])

        activity_data['points'] = all_points

        if all_points:
            # If we have time data, use it
            if all_points[-1]['elapsed_time'] > 0:
                activity_data['total_duration'] = all_points[-1]['elapsed_time']
            else:
                # No time data - estimate based on distance and assumed average speed (15 km/h)
                # Or use point count with 1 second interval
                if activity_data['total_distance'] > 0:
                    # Estimate duration: assume average speed of 15 km/h (4.17 m/s)
                    assumed_speed_ms = 15 / 3.6  # 15 km/h in m/s
                    estimated_duration = activity_data['total_distance'] / assumed_speed_ms
                    activity_data['total_duration'] = estimated_duration

                    # Recalculate elapsed_time for each point based on distance proportion
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

            activity_data['avg_speed'] = (activity_data['total_distance'] / activity_data['total_duration'] * 3.6) if activity_data['total_duration'] > 0 else 0

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
