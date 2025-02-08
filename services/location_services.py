import googlemaps
import os
from geopy.geocoders import Nominatim

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


print(os.getenv("GOOGLE_MAPS_API_KEY"))  # Ensure it's not None


def get_coordinates(location):
    """Fetch latitude, longitude, city, and state code using Google Maps API."""
    if not location or not GOOGLE_MAPS_API_KEY:
        return None, None, None, None  # Ensure function always returns four values

    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

    try:
        geocode_result = gmaps.geocode(location)

        if geocode_result and len(geocode_result) > 0:
            lat = geocode_result[0]["geometry"]["location"]["lat"]
            lng = geocode_result[0]["geometry"]["location"]["lng"]

            city, state_code = None, None
            for component in geocode_result[0]["address_components"]:
                if "administrative_area_level_1" in component["types"]:
                    state_code = component["short_name"]  # e.g., "CA"
                if "locality" in component["types"]:
                    city = component["long_name"]  # e.g., "San Francisco"

            return lat, lng, city, state_code
        else:
            return None, None, None, None  # No valid response

    except Exception as e:
        print(f"Google Maps API Error: {e}")
        return None, None, None, None


def get_coordinates_311(location):
  
    """
    Convert a city name or ZIP code into latitude & longitude.
    """
    geolocator = Nominatim(user_agent="waste_management_app")
    try:
        location_data = geolocator.geocode(location)
        if location_data:
            return location_data.latitude, location_data.longitude  # ✅ Only return lat & lng
        else:
            return None, None  # ✅ Ensure exactly 2 values are returned
    except:
        return None, None  # ✅ Avoid error if API fails


    
    
