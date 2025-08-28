import streamlit as st
import requests

BASE_URL = "https://api.gbif.org/v1"
ROOT_KINGDOMS = ["Animalia", "Plantae", "Fungi"]

# Utility to get taxonKey from name + rank
@st.cache_data(show_spinner=False)
def get_taxon_key(name, rank="kingdom"):
    url = f"{BASE_URL}/species/match"
    params = {"name": name, "rank": rank.upper()}
    r = requests.get(url, params=params)
    if r.ok:
        return r.json().get("usageKey")
    return None

# Fetch children for given taxonKey
@st.cache_data(show_spinner=False)
def get_children(taxon_key):
    url = f"{BASE_URL}/species/{taxon_key}/children"
    r = requests.get(url, params={"limit": 100})
    if r.ok:
        return r.json().get("results", [])
    return []

# Convert children data to tree nodes for streamlit_tree_select
def format_children(children):
    nodes = []
    for child in children:
        nodes.append({
            "id": str(child["key"]),
            "label": f"{child.get('canonicalName', child.get('scientificName', 'Unknown'))} ({child.get('rank', '')})",
            "hasChildren": child.get("numDescendants", 0) > 0
        })
    return nodes

# Build root nodes for kingdoms
def get_root_nodes():
    roots = []
    for kingdom in ROOT_KINGDOMS:
        key = get_taxon_key(kingdom)
        if key:
            roots.append({
                "id": str(key),
                "label": kingdom,
                "hasChildren": True,
            })
    return roots

# Streamlit UI
st.title("🌳 Dynamic GBIF Tree of Life Navigator")

import streamlit_tree_select

# Get or initialize expanded nodes state
if "expanded_nodes" not in st.session_state:
    st.session_state.expanded_nodes = set()

# Define callback for node expansion
def on_expand(node_id):
    st.session_state.expanded_nodes.add(node_id)

# Get root nodes or nodes under selected node
selected_nodes = st.session_state.get("selected_nodes", [])

root_nodes = get_root_nodes()

# Function to build a subtree dynamically for a given node id
def build_subtree(node_id):
    children = get_children(node_id)
    return format_children(children)

# Display the tree selector
selected = streamlit_tree_select.tree_select(
    tree=root_nodes,
    max_selections=1,
    key="tree_select",
    on_expand=on_expand,
    expanded_nodes=list(st.session_state.expanded_nodes),
    format_func=lambda x: x["label"],
    lazy_load=build_subtree
)

st.write("You selected taxonKey:", selected)

if selected:
    st.markdown(f"## Occurrences for taxonKey: {selected}")
    # Here you can add code to query GBIF occurrence API and plot etc.
