import streamlit as st
import requests

BASE_URL = "https://api.gbif.org/v1"
ROOT_KINGDOMS = ["Animalia", "Plantae", "Fungi"]

@st.cache_data(show_spinner=False)
def get_taxon_key(name, rank="kingdom"):
    url = f"{BASE_URL}/species/match"
    params = {"name": name, "rank": rank.upper()}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("usageKey")
    return None

@st.cache_data(show_spinner=False)
def get_children(taxon_key):
    url = f"{BASE_URL}/species/{taxon_key}/children"
    r = requests.get(url, params={"limit": 100})
    if r.ok:
        return r.json().get("results", [])
    return []

def format_children(children):
    nodes = []
    for child in children:
        nodes.append({
            "id": str(child["key"]),
            "label": f"{child.get('canonicalName', child.get('scientificName', 'Unknown'))} ({child.get('rank', '')})",
            "num_children": child.get("numDescendants", 0)
        })
    return nodes

st.title("🌳 Dynamic GBIF Tree of Life Navigator")

roots = []
for kingdom in ROOT_KINGDOMS:
    key = get_taxon_key(kingdom)
    if key:
        roots.append({"key": key, "name": kingdom})

# Simple expandable tree using Streamlit expanders
def display_tree(taxon_key, name, level=0):
    children = get_children(taxon_key)
    exp_label = f"{name} (children: {len(children)})"
    with st.expander(exp_label, expanded=level < 1):
        for child in children:
            child_key = child["key"]
            child_name = child.get("canonicalName") or child.get("scientificName")
            if child.get("numDescendants", 0) > 0:
                display_tree(child_key, child_name, level + 1)
            else:
                st.write(f"- {child_name} ({child.get('rank')})")

for root in roots:
    display_tree(root["key"], root["name"])

