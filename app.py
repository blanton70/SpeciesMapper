from flask import Flask, request, send_file
import folium
from folium.plugins import HeatMap
import pandas as pd
import requests
import time

app = Flask(__name__)

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

@app.route("/query")
def query():
    family = request.args.get("family")
    taxon_key = get_taxon_key(family)
    df = get_occurrences(taxon_key)
    df["lat_bin"] = (df["lat"] // 1) * 1
    df["lon_bin"] = (df["lon"] // 1) * 1
    richness = df.groupby(["lat_bin", "lon_bin"])["species"].nunique().reset_index()
    richness.columns = ["lat", "lon", "richness"]

    m = folium.Map(location=[0, 0], zoom_start=2)
    heat_data = [[row["lat"], row["lon"], row["richness"]] for _, row in richness.iterrows()]
    HeatMap(heat_data, radius=8).add_to(m)
    m.save("templates/map.html")
    return send_file("templates/map.html")

if __name__ == "__main__":
    app.run(debug=True)
