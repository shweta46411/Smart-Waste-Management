import requests
from config.settings import IWASTE_API_URL


def get_waste_facilities():
    """Fetches available waste disposal facilities."""
    response = requests.get(f"{IWASTE_API_URL}/facilities")
    return response.json() if response.status_code == 200 else {"error": "No facilities found"}

def get_disposal_facility_types():
    """Fetches disposal facility types."""
    response = requests.get(f"{IWASTE_API_URL}/disposal-facility-subtypes")
    return response.json() if response.status_code == 200 else {"error": "No facility types available"}


