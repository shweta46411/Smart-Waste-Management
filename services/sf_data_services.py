import requests
import pandas as pd
import streamlit as st
import os
from geopy.distance import geodesic

# ✅ Load API Keys Securely
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Fetch from environment variables
SF_PIT_STOP_API_URL = "https://data.sfgov.org/resource/mr6h-cr3u.json"
GOOGLE_GEOCODING_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"

@st.cache_data
def fetch_pit_stop_data():
    """Fetch public restroom (Pit Stop) data from San Francisco API."""
    response = requests.get(SF_PIT_STOP_API_URL)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    return pd.DataFrame()

def process_pit_stop_data(df):
    """Process the fetched data for analysis & visualization."""
    if df.empty:
        return None

    df["latitude"] = df["location"].apply(lambda x: x["coordinates"][1] if isinstance(x, dict) and "coordinates" in x else None)
    df["longitude"] = df["location"].apply(lambda x: x["coordinates"][0] if isinstance(x, dict) and "coordinates" in x else None)
    
    return df.dropna(subset=["latitude", "longitude"])  # ✅ Remove rows with missing coordinates

def get_cleaned_pit_stop_data():
    """Fetch and process data in one step."""
    df = fetch_pit_stop_data()
    return process_pit_stop_data(df)

def get_coordinates(address):
    """Convert user’s address to latitude & longitude using Google Geocoding API."""
    if not GOOGLE_MAPS_API_KEY:
        st.error("⚠️ Missing Google Maps API Key.")
        return None, None

    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
    response = requests.get(GOOGLE_GEOCODING_API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            location = data["results"][0]["geometry"]["location"]
            lat, lng = location["lat"], location["lng"]
            print(f"📍 Geocoding Debug: {address} -> {lat}, {lng}")  # Debugging
            return lat, lng

    return None, None

def filter_nearby_pit_stops(user_lat, user_lng, df, max_distance_km=5):
    """Find Pit Stops within a given radius of the user's location."""
    nearby_stops = []
    
    for _, row in df.iterrows():
        pit_stop_location = (row["latitude"], row["longitude"])
        user_location = (user_lat, user_lng)
        distance = geodesic(user_location, pit_stop_location).km

        print(f"🚀 Checking Pit Stop: {row['name']} -> Distance: {distance:.2f} km")  # Debugging

        if distance <= max_distance_km:
            nearby_stops.append(row)

    return pd.DataFrame(nearby_stops)

