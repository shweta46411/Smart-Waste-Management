import pandas as pd
import requests
import os
import streamlit as st
from config.settings import STREET_MAINTENANCE  # Import API URLs dynamically
import folium
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_folium import folium_static
from geopy.distance import geodesic


CACHE_FILE = "cached_street_data.csv"

# ✅ Fetch API Data with Structured Query Parameters & Pagination
@st.cache_data(ttl=3600)  # Cache API data for 1 hour
def fetch_api_data():
    """Fetches waste management data from API, with pagination and structured parameters."""
    url = STREET_MAINTENANCE
    
    params = {
        "limit": 1000,  # Fetch large chunks of data if applicable
        "offset": 0,  # Used for pagination if API supports it
    }
    
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        
        if not data:  # If API returns an empty dataset
            st.warning("⚠️ API returned no data.")
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Debugging: Show sample data
        st.write("✅ API Data Sample:", df.head(3))

        return df  # Convert API response to DataFrame
    
    else:
        st.error(f"⚠️ API Error: {response.status_code}")
        return pd.DataFrame()

# ✅ Load Data Efficiently with Local Caching
def load_data():
    if os.path.exists(CACHE_FILE):
        
        return pd.read_csv(CACHE_FILE)
    
    df = fetch_api_data()

    if not df.empty:
        df.to_csv(CACHE_FILE, index=False)  # Save data locally
    else:
        st.warning("⚠️ No data available to cache.")

    return df

# ✅ Preprocess Data
def preprocess_data(df):
    if df.empty:
        return df  # Return empty DataFrame if no data

    # Convert columns to numeric
    numeric_cols = [
        "how_many_instances_of_graffiti", "how_many_instances_of_feces",
        "how_many_large_abandoned", "how_many_abandoned_syringes"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["creationdate"] = pd.to_datetime(df["creationdate"])

    # Mapping Coded Values to Readable Categories
    route_type_mapping = {"1": "Commercial", "2": "Residential", "3": "Industrial"}
    cleanliness_mapping = {"1": "Very Clean", "2": "Moderate Litter", "3": "Litter Accumulation", "4": "Severely Dirty"}

    df["route_type"] = df["is_this_route_predominantly"].map(route_type_mapping)
    df["cleanliness_level"] = df["select_the_statement_that"].map(cleanliness_mapping)

    return df

# ✅ Fetch & Process Data
def get_cleaned_data():
    df = load_data()
    return preprocess_data(df)

# ✅ Analytics Functions
def get_trend_data(df):
    if df.empty:
        return pd.DataFrame()
    
    df["month"] = pd.to_datetime(df["creationdate"]).dt.to_period("M")

    # Ensure numeric conversion
    numeric_cols = ["how_many_instances_of_graffiti", "how_many_instances_of_feces"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    # Group by month and sum the values
    trend_df = df.groupby("month")[numeric_cols].sum()

    # Ensure index is converted back to string for plotting
    trend_df.index = trend_df.index.astype(str)

    return trend_df

def get_high_risk_areas(df):
    if df.empty:
        return pd.DataFrame()
    
    return df[(df["how_many_instances_of_graffiti"] > 10) | (df["how_many_instances_of_feces"] > 5)]




SF_311_API_URL = "https://data.sfgov.org/resource/vw6y-z8j6.json"

def get_sf_311_data():
    """Fetch SF 311 waste complaints and return as a DataFrame."""
    response = requests.get(SF_311_API_URL)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)

        # ✅ Keep only relevant columns
        df = df[["service_subtype", "service_details", "address", "lat", "long", "neighborhoods_sffind_boundaries"]]
        df.dropna(subset=["lat", "long", "neighborhoods_sffind_boundaries"], inplace=True)

        # ✅ Convert lat/long to float
        df["lat"] = df["lat"].astype(float)
        df["long"] = df["long"].astype(float)

        return df
    else:
        return pd.DataFrame()

def get_top_complaint_locations(df, top_n=10):
    """Get the top complaint locations (neighborhoods) based on frequency."""
    top_neighborhoods = (
        df.groupby("neighborhoods_sffind_boundaries")
        .agg(
            total_reports=("address", "count"),
            common_complaint=("service_subtype", lambda x: x.mode().iloc[0] if not x.empty and not x.mode().empty else "Unknown")
        )
        .reset_index()
        .sort_values(by="total_reports", ascending=False)
        .head(top_n)
    )
    return top_neighborhoods

def generate_top_complaint_map(df, top_locations):
    """Generate a map of the top complaint locations."""
    if df.empty or top_locations.empty:
        return None

    sf_map = folium.Map(location=[37.7749, -122.4194], zoom_start=12)

    for _, row in top_locations.iterrows():
        # Get representative coordinates from SF 311 data for this neighborhood
        neighborhood_df = df[df["neighborhoods_sffind_boundaries"] == row["neighborhoods_sffind_boundaries"]]
        lat, lng = neighborhood_df[["lat", "long"]].mean()  # Use average coordinates to represent the area

        folium.Marker(
            [lat, lng],
            popup=f"<b>{row['neighborhoods_sffind_boundaries']}</b><br>Reports: {row['total_reports']}<br>Common Issue: {row['common_complaint']}",
            tooltip=row["neighborhoods_sffind_boundaries"],
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(sf_map)

    return sf_map
