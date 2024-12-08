import math
import requests

def arcgis_to_gmaps(x, y):
    R = 6378137  # Earth's radius in meters

    # Convert longitude
    longitude = (x / R) * (180 / math.pi)

    # Convert latitude
    latitude = math.degrees(math.atan(math.sinh(y / R)))

    return latitude, longitude

def gmaps_to_arcgis(latitude, longitude):
    R = 6378137  # Earth's radius in meters

    # Convert longitude to Web Mercator x
    x = math.radians(longitude) * R

    # Convert latitude to Web Mercator y
    y = math.log(math.tan((math.pi / 4) + math.radians(latitude) / 2)) * R

    return x, y

def get_distance_google_maps(api_key, origin, destination, mode="driving"):
    """
    Get the distance between two points using Google Maps Distance Matrix API.

    Parameters:
        api_key (str): Google Maps API key.
        origin (str): Origin location (latitude,longitude or address).
        destination (str): Destination location (latitude,longitude or address).
        mode (str): Travel mode (driving, walking, bicycling, transit).

    Returns:
        dict: Distance and travel time.
    """
    # Google Maps Distance Matrix API endpoint
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # Query parameters
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "units":"imperial",
        "key": api_key
    }

    # Make the request
    response = requests.get(url, params=params)

    # Parse the response
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            result = data["rows"][0]["elements"][0]
            if result["status"] == "OK":
                 # Extract and convert distance and duration
                distance_text = result["distance"]["text"] 
                duration_text = result["duration"]["text"]  

                # Extract numeric values
                distance = float(distance_text.split()[0]) 
                duration = float(duration_text.split()[0]) 

                return distance, duration
            else:
                return False
        else:
            return False
    else:
        return False
