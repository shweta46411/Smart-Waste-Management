import folium

def get_waste_disposal_locations():
    """Returns a list of waste disposal locations in San Francisco."""
    return [
    {
        "name": "Recology San Francisco Transfer Station",
        "lat": 37.7403,
        "lon": -122.3963,
        "address": "501 Tunnel Ave, San Francisco, CA 94134",
        "contact": "415-330-1400",
        "hours": {
            "Monday-Friday": "7:00 AM - 4:30 PM",
            "Saturday": "7:30 AM - 4:00 PM",
            "Sunday": "7:30 AM - 4:00 PM"
        }
    },
    {
        "name": "San Francisco Household Hazardous Waste Collection Facility",
        "lat": 37.7405,
        "lon": -122.3961,
        "address": "501 Tunnel Ave, San Francisco, CA 94134",
        "contact": "415-330-1405",
        "hours": {
            "Thursday-Saturday": "8:00 AM - 4:00 PM"
        }
    },
    {
        "name": "Recology's Recycle Central at Pier 96",
        "lat": 37.7473,
        "lon": -122.3748,
        "address": "Pier 96, San Francisco, CA",
        "contact": "415-621-6200",
        "hours": "Varies, contact for details"
    },
    {
        "name": "Valley Services",
        "lat": 37.7804,
        "lon": -122.4057,
        "address": "San Francisco, CA",
        "contact": "N/A",
        "hours": "N/A"
    },
    {
        "name": "The Junkluggers Of San Francisco & The Peninsula",
        "lat": 37.7600,
        "lon": -122.4330,
        "address": "San Francisco, CA",
        "contact": "415-231-6262",
        "hours": "Varies, call for availability"
    },
    {
        "name": "Blue Line Transfer",
        "lat": 37.6550,
        "lon": -122.4032,
        "address": "500 E Jamie Ct, South San Francisco, CA 94080",
        "contact": "650-589-4020",
        "hours": {
            "Monday-Friday": "6:00 AM - 4:30 PM",
            "Saturday": "8:00 AM - 4:30 PM",
            "Sunday": "Closed"
        }
    },
    {
        "name": "San Francisco Department of the Environment",
        "lat": 37.7823,
        "lon": -122.4193,
        "address": "1455 Market St #1200, San Francisco, CA 94103",
        "contact": "415-355-3700",
        "hours": "Office hours vary, check website"
    },
    {
        "name": "South San Francisco Scavenger Company",
        "lat": 37.6531,
        "lon": -122.4075,
        "address": "500 E Jamie Ct, South San Francisco, CA 94080",
        "contact": "650-589-4020",
        "hours": {
            "Monday-Friday": "6:00 AM - 4:30 PM",
            "Saturday": "8:00 AM - 4:30 PM",
            "Sunday": "Closed"
        }
    }
]

def create_sf_map():
    """Creates and returns a Folium map of San Francisco waste disposal locations."""
    
    # Create a map centered on San Francisco
    sf_map = folium.Map(location=[37.7749, -122.4194], zoom_start=12)

    # Get location data
    locations = get_waste_disposal_locations()

    # Add waste disposal locations as markers
    for location in locations:
        folium.Marker(
            [location["lat"], location["lon"]],
            popup=f"<b>{location['name']}</b><br>{location['address']}",
            tooltip=location["name"],
            icon=folium.Icon(color="green", icon="trash"),
        ).add_to(sf_map)

    return sf_map
