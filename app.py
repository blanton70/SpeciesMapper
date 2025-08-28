import requests
import streamlit as st

BASE_URL = "https://api.gbif.org/v1"

st.set_page_config(page_title="GBIF Dynamic Taxonomy Tree", layout="wide")
st.title("🌳 GBIF Dynamic Taxonomic Tree (Lazy-Loaded)")

# Ranks ordered by hierarchy
RANK_ORDER = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]

# Caching API calls for performance
@st.cache_data(show_spinner=False)
def get_taxon_key(name, rank="KINGDOM"):
    url = f"{BASE_URL}/species/match"
    r = requests.get(url, params={"name": name, "rank": rank})
    if r.ok:
        return r.json().get("usageKey")
    return None

@st.cache_data(show_spinner=False)
def get_children(taxon_key, limit=100, offset=0):
    url = f"{BASE_URL}/species/{taxon_key}/children"
    r = requests.get(url, params={"limit": limit, "offset": offset})
    if r.ok:
        return r.json().get("results", [])
    return []

@st.cache_data(show_spinner=False)
def get_all_children(taxon_key):
    """Retrieve all children with pagination."""
    all_children = []
    limit = 100
    offset = 0
    while True:
        children = get_children(taxon_key, limit, offset)
        if not children:
            break
        all_children.extend(children)
        if len(children) < limit:
            break
        offset += limit
    return all_children

def next_rank(current_rank):
    """Get the next lower rank in the GBIF hierarchy."""
    try:
        idx = RANK_ORDER.index(current_rank.lower())
        return RANK_ORDER[idx + 1] if idx + 1 < len(RANK_ORDER) else None
    except ValueError:
        return None

def display_node(name, key, rank, level=0):
    """Recursively display a node and lazy-load its children."""
    indent = " " * (level * 4)
    with st.expander(f"{indent}{name} (rank: {rank})", expanded=False):
        nrank = next_rank(rank)
        if not nrank:
            st.write(f"{indent}Reached terminal rank.")
            return

        children = get_all_children(key)
        filtered = [c for c in children if c.get("rank", "").lower() == nrank]

        # Optionally sort alphabetically
        filtered.sort(key=lambda x: x.get("canonicalName", ""))

        if not filtered:
            st.info(f"No children of rank '{nrank}' found.")
            return

        for child in filtered:
            child_name = child.get("canonicalName") or child.get("scientificName") or "Unknown"
            child_key = child.get("key")
            child_rank = child.get("rank") or nrank
            display_node(child_name, child_key, child_rank, level + 1)

# Start with root taxa
root_taxa = ["Animalia", "Plantae", "Fungi"]

for root in root_taxa:
    key = get_taxon_key(root)
    if key:
        display_node(root, key, "kingdom")
    else:
        st.error(f"Could not fetch key for {root}")
