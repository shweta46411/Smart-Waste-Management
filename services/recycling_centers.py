import googlemaps
from config.settings import GOOGLE_MAPS_API_KEY
import requests
from config.settings import IWASTE_API_URL
import streamlit as st 
import os
import pandas as pd
import openai
from geopy.distance import geodesic

def get_disposal_facilities(state_code, facility_type_id):
    """Fetches the nearest disposal facilities based on state and selected type."""
    if not state_code or not facility_type_id:
        return {"error": "Missing parameters, cannot fetch disposal facilities."}

    url = f"{IWASTE_API_URL}/facilities?stateCode={state_code}&facilityTypeId={facility_type_id}"

    response = requests.get(url)
    #st.write(f"API Request: {url}")  # Debugging
    #st.write(f"API Status Code: {response.status_code}")  # Debugging

    if response.status_code == 200:
        data = response.json()
        #st.write(f"API Response: {data}")  # Debugging
        
        return data.get("data", [])  # Extract 'data' list from response

    return {"error": "No facilities found for this state and facility type."}



GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_nearby_disposal_sites(lat, lng, radius_km):
    """Fetch nearby waste disposal sites using Google Maps API."""
    
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_km * 1000,  # Convert to meters
        "keyword": "waste disposal recycling center",
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(url, params=params)
    results = response.json().get("results", [])

    data = []
    for result in results:
        data.append({
            "name": result.get("name", "Unknown"),
            "lat": result["geometry"]["location"]["lat"],
            "lng": result["geometry"]["location"]["lng"],
            "type": result.get("types", ["Unknown"])[0]
        })

    return pd.DataFrame(data)



SF_311_API_URL = "https://data.sfgov.org/resource/vw6y-z8j6.json"

def get_sf_311_data():
    """Fetch SF 311 waste complaints and return as a DataFrame."""
    response = requests.get(SF_311_API_URL)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)

        # ✅ Ensure required columns exist
        required_cols = ["service_subtype", "service_details", "address", "lat", "long"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None  # Add missing columns if they don't exist

        df.dropna(subset=["lat", "long", "address"], inplace=True)

        # ✅ Convert lat/long to float
        df["lat"] = df["lat"].astype(float)
        df["long"] = df["long"].astype(float)

        # ✅ Fill missing service details
        df["service_details"] = df["service_details"].fillna("General Waste")

        return df
    else:
        return pd.DataFrame()

def get_ai_suggested_disposal_sites(user_lat, user_lng, radius_km):
    """Use AI to suggest waste disposal sites based on SF 311 trends."""
    
    df = get_sf_311_data()

    # ✅ Check if the dataset is empty
    if df.empty:
        return "⚠️ No SF 311 data available to generate recommendations."

    # ✅ Identify locations with frequent dumping
    disposal_sites = df.groupby("address").agg({
        "lat": "first",
        "long": "first",
        "service_details": lambda x: x.mode().iloc[0] if not x.empty and not x.mode().empty else "General Waste"
    }).reset_index()

    # ✅ Filter by distance
    disposal_sites["distance_km"] = disposal_sites.apply(
        lambda row: geodesic((user_lat, user_lng), (row["lat"], row["long"])).km, axis=1
    )
    
    disposal_sites = disposal_sites[disposal_sites["distance_km"] <= radius_km]

    # ✅ Generate AI-powered recommendations
    recommendations = generate_ai_recommendation(disposal_sites)

    return disposal_sites, recommendations

def generate_ai_recommendation(disposal_sites):
    """Use OpenAI to generate a recommendation based on disposal trends."""
    
    if disposal_sites.empty:
        return "⚠️ No waste disposal data found for recommendations."

    disposal_summary = "\n".join([
        f"{row['address']} - Common Waste: {row['service_details']}" 
        for _, row in disposal_sites.iterrows()
    ])

    prompt = f"""
    You are an expert in waste management. Based on past disposal trends, 
    provide a list of recommended waste disposal locations from the data below.

    **Disposal Sites Data:**
    {disposal_summary}

    Instructions:
    - Suggest which sites are most effective for waste disposal.
    - Recommend the best place to dispose of different waste types.
    - Provide an eco-friendly disposal strategy.

    Provide a structured response.
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ AI recommendation error: {str(e)}"

import folium

# Create a map centered on San Francisco
sf_map = folium.Map(location=[37.7749, -122.4194], zoom_start=12)

# List of waste disposal locations in San Francisco
locations = [
    {"name": "Recology San Francisco Transfer Station", "lat": 37.7403, "lon": -122.3963},
    {"name": "San Francisco Household Hazardous Waste Collection Facility", "lat": 37.7405, "lon": -122.3961},
    {"name": "Recology's Recycle Central at Pier 96", "lat": 37.7473, "lon": -122.3748},
    {"name": "Valley Services", "lat": 37.7804, "lon": -122.4057},
    {"name": "The Junkluggers Of San Francisco & The Peninsula", "lat": 37.7600, "lon": -122.4330},
    {"name": "Blue Line Transfer", "lat": 37.6550, "lon": -122.4032},
    {"name": "San Francisco Department of the Environment", "lat": 37.7823, "lon": -122.4193},
    {"name": "South San Francisco Scavenger Company", "lat": 37.6531, "lon": -122.4075},
]

# Add markers to the map
for location in locations:
    folium.Marker(
        [location["lat"], location["lon"]],
        popup=location["name"],
        tooltip=location["name"],
        icon=folium.Icon(color="green", icon="trash"),
    ).add_to(sf_map)

# Save the map to an HTML file
sf_map.save("san_francisco_waste_map.html")

print("Map saved as 'san_francisco_waste_map.html'. Open this file in a browser to view it.")
