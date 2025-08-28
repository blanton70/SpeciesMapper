import streamlit as st
import requests
import pandas as pd
import json
import time
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium


# -------- Load tree -------- #
@st.cache_data
def load_tree():
    with open("tree.json") as f:
        return json.load(f)

tree = load_tree()

# -------- UI: Recursive Tree Menu -------- #
def show_tree(tree_node, path=[]):
    for key in tree_node:
        with st.expander(" > ".join(path + [key])):
            if tree_node[key]:
                show_tree(tree_node[key], path + [key])
            else:
                if st.button(f"Select {key}", key=">".join(path + [key])):
                    st.session_state["selected_family"] = key


st.title("🌍 GBIF Species Richness Mapper")
st.subheader("Step 1: Select a Family from the Tree")

if "selected_family" not in st.session_state:
    st.session_state["selected_family"] = None

show_tree(tree)

selected_family = st.session_state["selected_family"]

# -------- GBIF Occurrence Query -------- #
def get_taxon_key(family):
    url = f"https://api.gbif.org/v1/species/match?rank=FAMILY&name={family}"
    r = requests.get(url)
    return r.json().get("usageKey")

def get_occurrences(taxon_key):
    continents = {
        "Africa": {"lat_min": -35, "lat_max": 37, "lon_min": -18, "lon_max": 52},
        "Asia": {"lat_min": 0, "lat_max": 80, "lon_min": 26, "lon_max": 180},
        "Europe": {"lat_min": 35, "lat_max": 72, "lon_min": -25, "lon_max": 60},
        "North America": {"lat_min": 5, "lat_max": 84, "lon_min": -170, "lon_max": -50},
        "South America": {"lat_min": -60, "lat_max": 15, "lon_min": -90, "lon_max": -30},
        "Oceania": {"lat_min": -50, "lat_max": 0, "lon_min": 110, "lon_max": 180},
    }

    all_data = []
    for region, bbox in continents.items():
        url = "https://api.gbif.org/v1/occurrence/search"
        offset = 0
        limit = 300
        while len(all_data) < 1000:
            params = {
                "taxonKey": taxon_key,
                "has_coordinate": "true",
                "has_geospatial_issue": "false",
                "decimalLatitude": f"{bbox['lat_min']},{bbox['lat_max']}",
                "decimalLongitude": f"{bbox['lon_min']},{bbox['lon_max']}",
                "limit": limit,
                "offset": offset
            }
            r = requests.get(url, params=params)
            data = r.json().get("results", [])
            for o in data:
                if o.get("species") and o.get("decimalLatitude") and o.get("decimalLongitude"):
                    all_data.append({
                        "species": o["species"],
                        "lat": o["decimalLatitude"],
                        "lon": o["decimalLongitude"]
                    })
            offset += limit
            time.sleep(1)
    return pd.DataFrame(all_data)

# -------- Map Rendering -------- #
if selected_family:
    st.subheader(f"Step 2: Querying GBIF for `{selected_family}`")
    with st.spinner("Fetching data..."):
        taxon_key = get_taxon_key(selected_family)
        if taxon_key:
            df = get_occurrences(taxon_key)
            df["lat_bin"] = (df["lat"] // 1) * 1
            df["lon_bin"] = (df["lon"] // 1) * 1
            richness = df.groupby(["lat_bin", "lon_bin"])["species"].nunique().reset_index()
            richness.columns = ["lat", "lon", "richness"]

            m = folium.Map(location=[0, 0], zoom_start=2, tiles="cartodbpositron")
            heat_data = [[row["lat"], row["lon"], row["richness"]] for _, row in richness.iterrows()]
            HeatMap(heat_data, radius=8).add_to(m)

            st.subheader("🌐 Species Richness Map")
            st_folium(m, width=700, height=500)
        else:
            st.error(f"Could not find taxon key for '{selected_family}'")
