from fitparse import FitFile
from typing import Dict
from datetime import datetime


class FITParser:
    @staticmethod
    def parse(file_path: str) -> Dict:
        """Parse FIT file and extract activity data"""
        fitfile = FitFile(file_path)

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

        all_points = []
        start_time = None

        # Parse records
        for record in fitfile.get_messages('record'):
            point_data = {
                'latitude': None,
                'longitude': None,
                'elevation': None,
                'time': None,
                'elapsed_time': 0,
                'speed': 0,
                'distance': 0,
                'heart_rate': None,
                'cadence': None,
                'power': None,
            }

            for data in record:
                if data.name == 'position_lat':
                    # Convert semicircles to degrees
                    point_data['latitude'] = data.value * (180 / 2**31) if data.value else None
                elif data.name == 'position_long':
                    point_data['longitude'] = data.value * (180 / 2**31) if data.value else None
                elif data.name == 'altitude':
                    point_data['elevation'] = data.value
                elif data.name == 'timestamp':
                    point_data['time'] = data.value.isoformat() if data.value else None
                    if start_time is None:
                        start_time = data.value
                    if data.value and start_time:
                        point_data['elapsed_time'] = (data.value - start_time).total_seconds()
                elif data.name == 'speed':
                    # Speed is in m/s, convert to km/h
                    point_data['speed'] = data.value * 3.6 if data.value else 0
                elif data.name == 'distance':
                    point_data['distance'] = data.value if data.value else 0
                elif data.name == 'heart_rate':
                    point_data['heart_rate'] = data.value
                elif data.name == 'cadence':
                    point_data['cadence'] = data.value
                elif data.name == 'power':
                    point_data['power'] = data.value

            if point_data['latitude'] and point_data['longitude']:
                all_points.append(point_data)

        activity_data['points'] = all_points

        # Calculate statistics
        if all_points:
            # Calculate total distance first
            total_distance = 0
            for i in range(1, len(all_points)):
                from math import radians, cos, sin, asin, sqrt
                lat1, lon1 = all_points[i-1]['latitude'], all_points[i-1]['longitude']
                lat2, lon2 = all_points[i]['latitude'], all_points[i]['longitude']

                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371000  # Radius of earth in meters
                distance = c * r
                total_distance += distance

            activity_data['total_distance'] = total_distance

            # Set or estimate duration
            if all_points[-1]['elapsed_time'] > 0:
                activity_data['total_duration'] = all_points[-1]['elapsed_time']
                activity_data['has_time_data'] = True
            elif total_distance > 0:
                # Estimate duration: assume average speed of 15 km/h
                assumed_speed_ms = 15 / 3.6
                estimated_duration = total_distance / assumed_speed_ms
                activity_data['total_duration'] = estimated_duration

                # Recalculate elapsed_time for each point
                cumulative_distance = 0
                for i, point in enumerate(all_points):
                    if i > 0:
                        # Add distance from previous point
                        lat1, lon1 = all_points[i-1]['latitude'], all_points[i-1]['longitude']
                        lat2, lon2 = point['latitude'], point['longitude']
                        from math import radians, cos, sin, asin, sqrt
                        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                        dlon = lon2 - lon1
                        dlat = lat2 - lat1
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * asin(sqrt(a))
                        r = 6371000
                        distance = c * r
                        cumulative_distance += distance
                    point['elapsed_time'] = (cumulative_distance / total_distance) * estimated_duration if total_distance > 0 else 0
            else:
                # Fallback: 1 second per point
                activity_data['total_duration'] = len(all_points)
                for i, point in enumerate(all_points):
                    point['elapsed_time'] = i

            # Speed statistics
            speeds = [p['speed'] for p in all_points if p['speed'] > 0]
            if speeds:
                activity_data['max_speed'] = max(speeds)
                activity_data['avg_speed'] = sum(speeds) / len(speeds)

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
