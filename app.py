import requests
import streamlit as st

BASE_URL = "https://api.gbif.org/v1"

def get_taxon_key(name, rank="KINGDOM"):
    url = f"{BASE_URL}/species/match"
    params = {"name": name, "rank": rank}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("usageKey")
    return None

def get_children(taxon_key, limit=100, offset=0):
    url = f"{BASE_URL}/species/{taxon_key}/children"
    params = {"limit": limit, "offset": offset}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("results", [])
    return []

def get_immediate_children(taxon_key):
    """Fetch all immediate children (with pagination)"""
    all_children = []
    limit = 100
    offset = 0
    while True:
        children = get_children(taxon_key, limit=limit, offset=offset)
        if not children:
            break
        all_children.extend(children)
        if len(children) < limit:
            break
        offset += limit
    return all_children

def display_node(name, taxon_key, level=0):
    indent = " " * (level * 4)
    with st.expander(f"{indent}{name} (key: {taxon_key})"):
        # Button to load children
        if st.button(f"Load children of {name}", key=f"load-{taxon_key}"):
            children = get_immediate_children(taxon_key)
            if not children:
                st.write(f"{indent}No children found.")
            else:
                for child in children:
                    child_name = child.get("canonicalName") or child.get("scientificName") or "Unknown"
                    child_key = child.get("key")
                    display_node(child_name, child_key, level=level+1)

st.title("🌳 GBIF Lazy-Loading Taxonomy Tree")

# Root kingdoms
root_taxa = ["Animalia", "Plantae", "Fungi"]
root_keys = {}

for root in root_taxa:
    key = get_taxon_key(root)
    if key:
        root_keys[root] = key
    else:
        st.error(f"Could not find taxon key for {root}")

for root_name, root_key in root_keys.items():
    display_node(root_name, root_key)
