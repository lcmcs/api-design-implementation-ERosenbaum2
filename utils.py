"""
Utility functions for the Minyan Finder API.
"""
import math


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
    
    Returns:
        Distance in miles between the two points
    """
    # Earth's radius in miles
    R = 3959.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Calculate differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    # Distance in miles
    distance = R * c
    
    return distance


def validate_coordinates(latitude: float, longitude: float) -> tuple[bool, str]:
    """
    Validate that coordinates are within valid ranges.
    
    Args:
        latitude: Latitude to validate
        longitude: Longitude to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return False, "Latitude and longitude must be numbers"
    
    if latitude < -90 or latitude > 90:
        return False, "Latitude must be between -90 and 90"
    
    if longitude < -180 or longitude > 180:
        return False, "Longitude must be between -180 and 180"
    
    return True, ""


def validate_minyan_type(minyan_type: str) -> tuple[bool, str]:
    """
    Validate that minyan type is one of the allowed values.
    
    Args:
        minyan_type: Minyan type to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = ["shacharit", "mincha", "maariv"]
    if minyan_type not in valid_types:
        return False, f"Minyan type must be one of: {', '.join(valid_types)}"
    
    return True, ""

