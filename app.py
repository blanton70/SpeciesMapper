import requests
import streamlit as st

BASE_URL = "https://api.gbif.org/v1"

# Cache API calls for efficiency
@st.cache_data(show_spinner=False)
def get_taxon_key(name, rank="KINGDOM"):
    url = f"{BASE_URL}/species/match"
    params = {"name": name, "rank": rank}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("usageKey")
    return None

@st.cache_data(show_spinner=False)
def get_children(taxon_key, limit=100, offset=0):
    url = f"{BASE_URL}/species/{taxon_key}/children"
    params = {"limit": limit, "offset": offset}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("results", [])
    return []

@st.cache_data(show_spinner=False)
def get_all_children(taxon_key):
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

# Determine next rank in GBIF hierarchy (simplified)
RANK_ORDER = [
    "kingdom", "phylum", "class", "order", "family", "genus", "species"
]

def next_rank(current_rank):
    try:
        idx = RANK_ORDER.index(current_rank.lower())
        return RANK_ORDER[idx + 1] if idx + 1 < len(RANK_ORDER) else None
    except ValueError:
        return None

def display_taxon_node(name, taxon_key, current_rank, level=0):
    indent = " " * (level * 4)

    # Use an expander to display children dynamically
    with st.expander(f"{indent}{name} (rank: {current_rank}, key: {taxon_key})", expanded=False):
        # Get the next rank to fetch
        nrank = next_rank(current_rank)
        if not nrank:
            st.write(f"{indent}Reached lowest rank or unknown next rank.")
            return

        children = get_all_children(taxon_key)

        # Filter children to only immediate children of next rank
        filtered = [c for c in children if c.get("rank", "").lower() == nrank]

        if not filtered:
            st.write(f"{indent}No children of rank '{nrank}' found.")
            return

        for child in filtered:
            child_name = child.get("canonicalName") or child.get("scientificName") or "Unknown"
            child_key = child.get("key")
            child_rank = child.get("rank") or nrank
            display_taxon_node(child_name, child_key, child_rank, level + 1)

st.title("🌳 GBIF Hierarchical Tree - Lazy Load by Rank")

# Initialize session state to keep track of root keys
if "root_taxa" not in st.session_state:
    st.session_state.root_taxa = {}

root_taxa_names = ["Animalia", "Plantae", "Fungi"]

# Get root keys and ranks once
for root in root_taxa_names:
    if root not in st.session_state.root_taxa:
        key = get_taxon_key(root, rank="KINGDOM")
        st.session_state.root_taxa[root] = {"key": key, "rank": "kingdom"}

for root_name, info in st.session_state.root_taxa.items():
    if info["key"]:
        display_taxon_node(root_name, info["key"], info["rank"])
    else:
        st.error(f"Could not find taxon key for {root_name}")
