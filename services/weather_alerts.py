import requests
import streamlit as st
from config.settings import OPENWEATHER_API_KEY, OPENWEATHER_API_URL  # Fetch API key and URL dynamically

# ✅ Cache API response for 30 minutes to reduce redundant API calls
@st.cache_data(ttl=1800)
def get_weather(city):
    """
    Fetches real-time weather data for a given city from OpenWeather API.

    Parameters:
        city (str): Name of the city for which weather data is requested.

    Returns:
        dict: Weather data response in JSON format or error message.
    """
    if not city:
        return {"error": "⚠️ Please provide a valid city name."}

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"  # Convert temperature to Celsius for readability
    }

    try:
        response = requests.get(OPENWEATHER_API_URL, params=params)
        response.raise_for_status()  # Raise an error for bad HTTP responses (4xx, 5xx)
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"⚠️ API Error: {e}"}

def format_weather_data(data):
    """
    Formats weather data for user-friendly display.

    Parameters:
        data (dict): Weather data fetched from OpenWeather API.

    Returns:
        str: Readable formatted weather report or an error message.
    """
    if "error" in data:
        return data["error"]

    try:
        return f"""
        🌍 **Location:** {data["name"]}, {data["sys"]["country"]}
        🌦️ **Weather:** {data["weather"][0]["description"].capitalize()}
        🌡️ **Temperature:** {data["main"]["temp"]}°C
        💧 **Humidity:** {data["main"]["humidity"]}%
        💨 **Wind Speed:** {data["wind"]["speed"]} m/s
        """
    except KeyError:
        return "⚠️ Error parsing weather data. Please try again."

def get_weather_alert(city):
    """
    Fetches weather conditions to determine potential waste collection delays.

    Parameters:
        city (str): City for which weather conditions are requested.

    Returns:
        str: Weather description with temperature details.
    """
    weather_data = get_weather(city)
    if "error" in weather_data:
        return weather_data["error"]

    try:
        weather_desc = weather_data["weather"][0]["description"]
        temp = round(weather_data["main"]["temp"], 2)
        return f"🌦️ **Weather:** {weather_desc.capitalize()}, 🌡️ **Temperature:** {temp}°C"
    except KeyError:
        return "⚠️ Weather data unavailable. Please check the city name and try again."
