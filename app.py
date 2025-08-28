import streamlit as st
import requests

BASE_URL = "https://api.gbif.org/v1"
ROOT_KINGDOMS = ["Animalia", "Plantae", "Fungi"]

RANK_HIERARCHY = [
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species"
]

@st.cache_data(show_spinner=False)
def get_taxon_key(name, rank="kingdom"):
    url = f"{BASE_URL}/species/match"
    params = {"name": name, "rank": rank.upper()}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("usageKey")
    return None

@st.cache_data(show_spinner=False)
def get_children(taxon_key, max_children=200):
    children = []
    limit = 100
    offset = 0

    while True:
        url = f"{BASE_URL}/species/{taxon_key}/children"
        params = {"limit": limit, "offset": offset}
        r = requests.get(url, params=params)
        if not r.ok:
            break
        batch = r.json().get("results", [])
        if not batch:
            break
        children.extend(batch)
        if len(children) >= max_children:
            break
        offset += limit

    return children[:max_children]

def get_next_rank(current_rank):
    try:
        idx = RANK_HIERARCHY.index(current_rank.lower())
        return RANK_HIERARCHY[idx + 1] if idx + 1 < len(RANK_HIERARCHY) else None
    except ValueError:
        return None

def get_rank_index(rank):
    try:
        return RANK_HIERARCHY.index(rank.lower())
    except ValueError:
        return -1

def display_tree(taxon_key, name, current_rank="kingdom", level=0):
    exp_label = f"{name} ({current_rank})"
    with st.expander(exp_label, expanded=level==0):
        children = get_children(taxon_key)
        if not children:
            st.write("— Leaf node")
            return

        curr_idx = get_rank_index(current_rank)
        for child in children:
            child_rank = child.get("rank", "").lower() or "unranked"
            child_name = child.get("canonicalName") or child.get("scientificName") or "Unknown"
            child_key = child["key"]

            child_idx = get_rank_index(child_rank)
            # Only recurse if child rank is lower (higher index) in hierarchy or unranked (-1)
            if child_idx == -1 or child_idx > curr_idx:
                display_tree(child_key, child_name, current_rank=child_rank, level=level+1)
            else:
                # Same or higher rank — treat as leaf here, just print
                st.markdown(f"{'  ' * (level + 1)}- {child_name} ({child_rank})")

st.title("🌳 Hierarchical GBIF Tree of Life Navigator")

roots = []
for kingdom in ROOT_KINGDOMS:
    key = get_taxon_key(kingdom)
    if key:
        roots.append({"key": key, "name": kingdom})

for root in roots:
    display_tree(root["key"], root["name"], current_rank="kingdom")
