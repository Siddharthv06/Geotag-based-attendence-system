"""
Geolocation utilities - Haversine formula for distance calculation
"""
import math


def distance_in_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two GPS points
    using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (in decimal degrees)
        lat2, lon2: Latitude and longitude of point 2 (in decimal degrees)

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_within_radius(
    user_lat: float,
    user_lon: float,
    site_lat: float,
    site_lon: float,
    radius_meters: int,
) -> tuple[bool, float]:
    """
    Check if a user is within the site's punch-in radius.

    Returns:
        (within_radius: bool, distance_meters: float)
    """
    dist = distance_in_meters(user_lat, user_lon, site_lat, site_lon)
    return dist <= radius_meters, round(dist, 2)
