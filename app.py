import streamlit as st
import io
import folium
from streamlit_folium import folium_static
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import services.weather_alerts as weather
import services.waste_classification as waste_classifier
import services.datasf_analytics_services as analytics
from services.recycling_centers import get_disposal_facilities
from services.location_services import get_coordinates, get_coordinates_311
import services.sf_data_services as sf_data
import services.datasf_analytics_services as data_sf
from services.sf_center import create_sf_map, get_waste_disposal_locations


# ----------- Streamlit UI Configuration ------------
st.set_page_config(
    page_title="♻️ Smart Waste Management",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------- Custom Styling ------------
def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

# ----------- Bin Image Mapping ------------
BIN_IMAGES = {
    "Recyclable": "assets/recology.bluebin.svg",
    "Compostable": "assets/recology.greenbin.svg",
    "Landfill": "assets/recology.blackbin.svg",
    "Hazardous": "assets/recology.hazardousbin.svg",
     "E-Waste": "assets/recology.hazardousbin.svg"
}

# ----------- App Header ------------
st.markdown("<h1 class='section-header'>♻️ Smart Waste Management System</h1>", unsafe_allow_html=True)
if "classification_result" not in st.session_state:
    st.session_state["classification_result"] = None

# ----------- Tabs ------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🗑 Waste Classification", "📍 SF Disposal Centers", "📊 Waste Analytics","🌉 SF Public Facility Data","US Disposal Facilities", "Weather Conditions"])

# ✅ Fetch Cleaned Data
df = analytics.get_cleaned_data()

# ----------- 1️⃣ Waste Classification ------------
with tab1:
    
    st.markdown("""
    <div class='section-header' style='text-align: center; font-size: 28px; font-weight: bold; color: #145a32;'>
        🗑 Waste Classification
    </div>
    """, unsafe_allow_html=True)
    
# Styled Input Selection - Side by Side
    st.markdown("""
    <div style='display: flex; justify-content: center; align-items: center; gap: 50px;'>
        <h4 style='font-size: 22px; color: #145a32;'>Choose Input Method:</h4>
        <div style='font-size: 20px;'>
     """, unsafe_allow_html=True)
    input_method = st.radio("", ["Type Waste Item", "Upload an Image"], index=0, horizontal=True)
    st.markdown("""
        </div>
    </div>
   """, unsafe_allow_html=True)
    

    if input_method == "Type Waste Item":
        waste_item = st.text_input("Enter a waste item (e.g., Plastic Bottle, Laptop, Battery):")
    
        if st.button("Classify Waste"):
            if waste_item:
                with st.spinner("Analyzing..."):
                    result = waste_classifier.classify_waste(waste_item)
                    category = result["category"]
                    bin_suggestion = result["bin"]
                    bin_image = BIN_IMAGES.get(category)
                    explanation = result["explanation"]


                st.info(f"**Category:** {category}")
                st.markdown("""
                <div class='explanation-container'>
                    <h3>📘 Explanation</h3>
                    <p>{}</p>
                </div>
                """.format(explanation), unsafe_allow_html=True)
                
                st.markdown("""
                <div class='bin-suggestion-container'>
                    <h3>🗑 Suggested Disposal Bin</h3>
                    <p><strong>{}</strong></p>
                </div>
                """.format(bin_suggestion), unsafe_allow_html=True)
                
                if bin_suggestion != "Unknown" and bin_image:
                    st.image(bin_image, caption=f"{bin_suggestion} Bin", width=150, output_format="SVG")
                else:
                    st.warning("⚠️ Unable to determine the correct bin. Please verify with local waste management guidelines.")


    elif input_method == "Upload an Image":
        uploaded_file = st.file_uploader("📤 Upload an image of waste", type=["jpg", "png", "jpeg"])

        if uploaded_file:
            image_bytes = io.BytesIO(uploaded_file.getvalue())
            image = Image.open(image_bytes)
            st.image(image, caption="Uploaded Image", width=300)

            if st.button("Analyze Waste"):
                with st.spinner("🔍 Analyzing Image..."):
                    result = waste_classifier.analyze_image(image_bytes)

                if "error" in result:
                    st.error(f"⚠️ {result['error']}")
                else:
                    category = result["category"]
                    bin_suggestion = result["bin"]
                    bin_image = BIN_IMAGES.get(category)
                    explanation = result["explanation"]

                    # Display Results
                    st.success(f"**Category:** {category}")
                    st.write("### 📘 Explanation:")
                    st.write(explanation)
                    
                    st.write("### 🗑 Suggested Disposal Bin:")
                    if bin_suggestion != "Unknown":
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.info(f"**{bin_suggestion}**")
                        with col2:
                            if bin_image:
                                st.image(bin_image, caption=f"{bin_suggestion} Bin", width=150, output_format="SVG")
                    else:
                        st.warning("⚠️ Unable to determine the correct bin. Please verify with local waste management guidelines.")


# ----------- 2️⃣ Find Disposal Centers ------------
# Facility type mapping
facility_types = {
    "Landfill": "1",
    "Recycling Center": "3",
    "Hazardous Waste Facility": "4",
    "Composting Facility": "5"
}

with tab5:
    st.markdown("""
    <div class='section-header' style='text-align: center; font-size: 28px; font-weight: bold; color: #145a32;'>
        📍 Find Disposal Centers
    </div>
    """, unsafe_allow_html=True)
    location = st.text_input("Enter a state or city:")
    facility_choice = st.selectbox("Select Facility Type:", list(facility_types.keys()))

    # ✅ Initialize `facilities`, `lat`, and `lng` to avoid "not defined" errors
    facilities = None
    lat, lng = None, None

    if st.button("Find Facilities"):
        if location:
            lat, lng, city, state_code = get_coordinates(location)

            if state_code is None:
                st.error("❌ Could not determine state. Please enter a valid city or ZIP code.")
            else:
                selected_type_id = facility_types[facility_choice]  # Get facility type ID
                facilities = get_disposal_facilities(state_code, selected_type_id)  # Fetch facilities

                if isinstance(facilities, list) and len(facilities) > 0:
                    st.markdown(f"<p class='big-font'>🏭 Available {facility_choice} Facilities:</p>", unsafe_allow_html=True)

                    for facility in facilities[:5]:  # Show top 5 results
                        facility_name = facility.get("name", "Unknown")
                        city = facility.get("city", "N/A")
                        state = facility.get("stateCode", "N/A")
                        facility_type = facility.get("facilitySubtypes", "Unknown Type")
                        phone = facility.get("contactPhone", "No Contact Info")

                        st.markdown(f"""
                        <div class='card'>
                            🏢 <b>{facility_name}</b>  
                            📍 {city}, {state}  
                            🏭 Type: {facility_type}  
                            📞 Contact: {phone}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"⚠️ No {facility_choice} facilities found for {state_code}.")
        else:
            st.warning("⚠️ Please enter a valid location before searching.")

    # ✅ Ensure `facilities` exists before using map visualization
    if facilities and isinstance(facilities, list) and len(facilities) > 0 and lat and lng:
        st.markdown("<h3 class='section-header'>🗺 Facility Locations on Map</h3>", unsafe_allow_html=True)

        # ✅ Add a map visualization (Folium)
        m = folium.Map(location=[lat, lng], zoom_start=8)

        for facility in facilities:
            fac_lat = facility.get("latitude", lat)
            fac_lng = facility.get("longitude", lng)
            facility_name = facility.get("name", "Unknown")

            folium.Marker(
                location=[fac_lat, fac_lng],
                popup=f"<b>{facility_name}</b>",
                icon=folium.Icon(color="green", icon="info-sign")
            ).add_to(m)

        folium_static(m)




   

# ----------- 4️⃣ Weather Conditions ------------
with tab6:
    st.markdown("""
    <div class='section-header' style='text-align: center; font-size: 28px; font-weight: bold; color: #145a32;'>
        ☀️ Weather Conditions
    </div>
    """, unsafe_allow_html=True)
    city = st.text_input("Enter a city name for weather information:")

    if st.button("Get Weather"):
        if city:
            with st.spinner("Fetching weather data..."):
                weather_data = weather.get_weather(city)
                formatted_weather = weather.format_weather_data(weather_data)
            st.markdown(f"### 🌍 Weather in {city}")
            st.info(formatted_weather)
        else:
            st.warning("⚠️ Please enter a valid city name.")



# ✅ Load SF Pit Stop Data
pit_stop_df = sf_data.get_cleaned_pit_stop_data()

# ✅ Add a New Tab for SF Data


# ----------- 4️⃣ San Francisco Waste & Public Facility  ------------
with tab4:
    
    st.markdown("""
    <div class='section-header' style='text-align: center; font-size: 28px; font-weight: bold; color: #145a32;'>
       🌉 San Francisco Public Facility Information
    </div>
    """, unsafe_allow_html=True)
    # 🔍 User Input for Searching Nearby Pit Stops
    user_location = st.text_input("Enter a location (ZIP, address, or city) to find nearby public restrooms:", "Union Square, San Francisco, CA")

    max_distance_km = st.slider("Select search radius (in km):", min_value=1, max_value=10, value=5)

    if st.button("Find Nearby Restrooms"):
        if user_location:
            with st.spinner("Fetching location..."):
                user_lat, user_lng = sf_data.get_coordinates(user_location)

            if user_lat and user_lng:
                st.success(f"📍 Located: {user_location} ({user_lat}, {user_lng})")

                # 🔍 Filter Nearby Pit Stops
                nearby_pit_stops = sf_data.filter_nearby_pit_stops(user_lat, user_lng, pit_stop_df, max_distance_km)

                if not nearby_pit_stops.empty:
                    st.markdown(f"### 🚻 Nearby Public Restrooms ({len(nearby_pit_stops)})")

                    # 🗺️ Display Map with Pit Stops
                    sf_map = folium.Map(location=[user_lat, user_lng], zoom_start=14)

                    # Add User Location Marker
                    folium.Marker(
                        [user_lat, user_lng],
                        popup="Your Location",
                        icon=folium.Icon(color="blue", icon="info-sign")
                    ).add_to(sf_map)

                    # Add Nearby Pit Stops
                    for _, row in nearby_pit_stops.iterrows():
                        folium.Marker(
                            [row["latitude"], row["longitude"]],
                            popup=f"{row['name']} - {row['address']} ({row['hours']})",
                            tooltip=row["name"],
                            icon=folium.Icon(color="green", icon="info-sign")
                        ).add_to(sf_map)

                    folium_static(sf_map)

                    # 🔥 **Meaningful Data Summary Instead of Raw Table**
                    st.markdown("## 📊 Key Insights About Nearby Public Restrooms")

                    # ✅ Total Pit Stops Found
                    st.metric("Total Pit Stops Nearby", len(nearby_pit_stops))

                    # ✅ Most Common Neighborhoods
                    common_neighborhoods = nearby_pit_stops["neighborhood"].value_counts().head(3)
                    neighborhood_summary = ", ".join([f"{n} ({c})" for n, c in common_neighborhoods.items()])
                    st.markdown(f"**🗺️ Most Common Neighborhoods:** {neighborhood_summary}")

                    # ✅ Average Operating Hours
                    avg_hours = nearby_pit_stops["hours"].value_counts().idxmax()  # Find most common hours
                    st.markdown(f"**⏳ Most Common Operating Hours:** {avg_hours}")

                    # ✅ Styled Table for Important Pit Stop Details
                    st.markdown("### 📍 Nearby Pit Stop Details")
                    st.table(nearby_pit_stops[["name", "address", "hours"]].reset_index(drop=True))

                else:
                    st.warning("⚠️ No public restrooms found nearby. Try a different location.")
            else:
                st.error("❌ Could not determine coordinates. Try a different location.")



  # ----------- 6️⃣ Waste Analytics Dashboard ------------
with tab3:
   
    st.markdown("""
    <div class='section-header' style='text-align: center; font-size: 28px; font-weight: bold; color: #145a32;'>
       🌉 San Francisco 📊 Waste Complaint Insights
    </div>
    """, unsafe_allow_html=True)
    with st.spinner("Fetching and analyzing waste complaint data..."):
        df_311 = data_sf.get_sf_311_data()

    if df_311.empty:
        st.error("❌ No SF 311 data available for analysis.")
    else:
        st.success(f"✅ Loaded {len(df_311)} waste complaints from SF 311 data.")

        # 🔍 Identify Top 10 Complaint Locations
        top_complaint_locations = data_sf.get_top_complaint_locations(df_311, top_n=10)

        if not top_complaint_locations.empty:
            st.markdown("### 🏙 Top 10 Neighborhoods with Most Waste Complaints")
            st.table(top_complaint_locations)

            # 🗺️ Generate Map with Top Complaint Locations
            st.markdown("### 🗺 Complaint Hotspots in San Francisco")
            top_map = data_sf.generate_top_complaint_map(df_311, top_complaint_locations)
            folium_static(top_map)

        else:
            st.warning("⚠️ No complaint locations found.")


# ----------- 2️⃣ Suggested Waste Disposal Locations ------------
with tab2:
    
    # Streamlit App Title
    
    st.markdown("""
    <div class='section-header' style='text-align: center; font-size: 28px; font-weight: bold; color: #145a32;'>
       📍 Disposal Centers
    </div>
    """, unsafe_allow_html=True)
    # Create two columns for layout (Details on left, Map on right)
    col1, col2 = st.columns([2, 3])
    
    # Column 1: List of Locations - Compact Layout
    with col1:
        locations = get_waste_disposal_locations()
        
        for loc in locations:
            hours = loc.get('hours', 'N/A')
            if isinstance(hours, dict):
                hours = ', '.join([f"{day}: {time}" for day, time in hours.items()])
            
            st.markdown(f"""
            <div class='location-card' style='display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-bottom: 1px solid #ddd;'>
                <div style='flex-grow: 1;'>
                    <h4 style='margin: 0; font-size: 18px;'>🏢 {loc['name']}</h4>
                    <p style='margin: 2px 0; font-size: 14px;'>📌 <strong>Address:</strong> {loc['address']}</p>
                    <p style='margin: 2px 0; font-size: 14px;'>📞 <strong>Contact:</strong> {loc.get('contact', 'N/A')}</p>
                    <p style='margin: 2px 0; font-size: 14px;'>⏰ <strong>Hours:</strong> {hours}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Column 2: Interactive Map
    with col2:
        st.markdown("<h3>🗺 Facility Locations</h3>", unsafe_allow_html=True)
        sf_map = create_sf_map()
        folium_static(sf_map)
    
    st.markdown("</div>", unsafe_allow_html=True)
