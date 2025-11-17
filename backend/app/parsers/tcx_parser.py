from tcxparser import TCXParser as TCXParserLib
from typing import Dict
from datetime import datetime


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
        }

        # Get activity data
        activity_data['total_distance'] = tcx.distance if tcx.distance else 0
        activity_data['total_duration'] = tcx.duration if tcx.duration else 0

        # Parse trackpoints
        start_time = None
        all_points = []

        for point in tcx.trackpoints:
            if start_time is None and point.time:
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
                'heart_rate': getattr(point, 'hr_value', None),
                'cadence': getattr(point, 'cadence', None),
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
