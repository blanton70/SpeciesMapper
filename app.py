import requests
import streamlit as st

BASE_URL = "https://api.gbif.org/v1"

MAX_DEPTH = 5  # Limit depth to avoid huge recursion; adjust as needed
MAX_CHILDREN = 200  # Limit children per node

@st.cache_data(show_spinner=False)
def get_children(taxon_key, limit=100, offset=0):
    url = f"{BASE_URL}/species/{taxon_key}/children"
    params = {"limit": limit, "offset": offset}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("results", [])
    return []

def fetch_all_children(taxon_key):
    all_children = []
    offset = 0
    limit = 100
    while True:
        batch = get_children(taxon_key, limit=limit, offset=offset)
        if not batch:
            break
        all_children.extend(batch)
        if len(all_children) >= MAX_CHILDREN:
            break
        offset += limit
    return all_children[:MAX_CHILDREN]

def build_tree(taxon_key, name, depth=0):
    if depth > MAX_DEPTH:
        return {"name": name, "key": taxon_key, "children": []}

    children = fetch_all_children(taxon_key)
    tree_children = []
    for child in children:
        child_name = child.get("canonicalName") or child.get("scientificName") or "Unknown"
        child_key = child["key"]
        subtree = build_tree(child_key, child_name, depth + 1)
        tree_children.append(subtree)

    return {"name": name, "key": taxon_key, "children": tree_children}

def display_tree_node(node, level=0):
    indent = " " * (level * 4)
    st.markdown(f"{indent}- {node['name']} (key: {node['key']})")
    for child in node.get("children", []):
        display_tree_node(child, level + 1)

st.title("🐾 GBIF Hierarchical Tree of Life")

root_taxa = ["Animalia", "Plantae", "Fungi"]

for root_name in root_taxa:
    # Get taxon key
    r = requests.get(f"{BASE_URL}/species/match", params={"name": root_name, "rank": "KINGDOM"})
    if r.ok:
        root_key = r.json().get("usageKey")
        if root_key:
            st.header(f"{root_name} (key: {root_key})")
            tree = build_tree(root_key, root_name)
            display_tree_node(tree)
        else:
            st.error(f"Could not find taxon key for {root_name}")
    else:
        st.error(f"API error getting taxon key for {root_name}")
