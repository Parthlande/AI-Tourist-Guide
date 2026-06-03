import streamlit as st
import pickle
import pandas as pd
import requests
from math import radians, sin, cos, sqrt, atan2

st.set_page_config(page_title="Tourist Guide", layout="centered")

# Load dataset
with open("places_dataset.pkl", "rb") as f:
    df = pickle.load(f)

# Haversine distance function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Get address from OpenStreetMap
def get_osm_address(lat, lon):
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "jsonv2", "lat": lat, "lon": lon},
            headers={"User-Agent": "AI-Tourist-Guide-App"}
        )
        data = response.json()
        return data.get("display_name", "Address not found")
    except:
        return "Address not found"

# Recommend nearby places
def recommend_places(city_name):
    city_row = df[df['Destination'].str.lower() == city_name.lower()]
    if city_row.empty:
        return None, None, None
    lat1, lon1 = city_row.iloc[0][['lat', 'lon']]
    df['distance'] = df.apply(lambda row: haversine(lat1, lon1, row['lat'], row['lon']), axis=1)
    nearby = df[df['Destination'].str.lower() != city_name.lower()].sort_values('distance')
    return nearby[['Destination', 'Category', 'Decription', 'lat', 'lon', 'distance']], lat1, lon1

# --- UI ---
st.title("🌐 AI Tourist Guide")
st.write("Choose a city to see nearby tourist spots with navigation, address, and AR View.")

cities = sorted(df['Destination'].unique())
selected_city = st.selectbox("📍 Choose your city:", cities)

if "num_places" not in st.session_state:
    st.session_state.num_places = 5

if st.button("🔍 Search Nearby Places"):
    result, lat1, lon1 = recommend_places(selected_city)
    if result is None or result.empty:
        st.warning(f"❌ No nearby places found for **{selected_city}**.")
    else:
        st.session_state.result = result
        st.session_state.lat1 = lat1
        st.session_state.lon1 = lon1
        st.session_state.num_places = 5

# Display Results
if "result" in st.session_state:
    result = st.session_state.result
    lat1 = st.session_state.lat1
    lon1 = st.session_state.lon1

    st.subheader(f"Nearby Places around **{selected_city}**:")

    for _, row in result.head(st.session_state.num_places).iterrows():
        address = get_osm_address(row['lat'], row['lon'])
        navigation_url = (
            f"https://www.openstreetmap.org/directions?"
            f"engine=fossgis_osrm_car&route={lat1}%2C{lon1}%3B{row['lat']}%2C{row['lon']}"
        )

        ar_url = (
            f"https://parthlande.github.io/AR/index.html?"
            f"lat={row['lat']}&lon={row['lon']}&name={row['Destination'].replace(' ', '%20')}"
        )

        st.markdown(
            f"""
            <div style="background-color: #f9f9f9; color: #000; padding: 15px;
                        border-radius: 10px; margin-bottom: 12px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #ccc;">
                <h4>🏞️ {row['Destination']}</h4>
                <p><strong>📌 Category:</strong> {row['Category']}</p>
                <p><strong>📝 Description:</strong> {row['Decription']}</p>
                <p><strong>📍 Address:</strong> {address}</p>
                <p><strong>📏 Distance:</strong> {row['distance']:.2f} km</p>
                <a href="{navigation_url}" target="_blank" style="
                    display: inline-block; margin-top: 10px; padding: 8px 16px;
                    background-color: #007BFF; color: white; text-decoration: none;
                    border-radius: 5px;">🧭 Navigate</a>
                <a href="{ar_url}" target="_blank" style="
                    display: inline-block; margin-top: 10px; margin-left: 10px; padding: 8px 16px;
                    background-color: #28a745; color: white; text-decoration: none;
                    border-radius: 5px;">🔍 AR View</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.session_state.num_places < len(result):
        if st.button("➕ Show 5 More"):
            st.session_state.num_places += 5
