import os
import streamlit as st
from dotenv import load_dotenv

RUNNING_IN_STREAMLIT = "STREAMLIT_SERVER_RUN_ONCE" in os.environ

# Securely fetch API keys
if RUNNING_IN_STREAMLIT:
    # ✅ Load from Streamlit Secrets in the cloud
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
    OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
    IWASTE_API_KEY = st.secrets["IWASTE_API_KEY"]
    print("🔹 Using Streamlit Secrets for API keys (Cloud Mode)")
else:
    # ✅ Load from .env file locally
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    IWASTE_API_KEY = os.getenv("IWASTE_API_KEY")
    print("🔹 Using .env file for API keys (Local Mode)")

# Load environment variables


# API Base URLs
IWASTE_API_URL = "https://iwaste.epa.gov/api"
GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
STREET_MAINTENANCE= "https://data.sfgov.org/resource/qya8-uhsz.json"