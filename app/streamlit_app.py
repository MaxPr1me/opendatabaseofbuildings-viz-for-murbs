"""Canadian MURB Geometry Analysis — Streamlit Visualization Application.

Launch with: streamlit run app/streamlit_app.py
"""

import json
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Canadian MURB Geometry Analysis",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 Canadian MURB Geometry Analysis")
st.subheader("Statistics Canada Open Database of Buildings — Visualization Tool")

# --- Sidebar: Filters ---
st.sidebar.header("Filters")

# Province selection
provinces = [
    "AB", "BC", "MB", "NB", "NL", "NS", "NT",
    "ON", "PE", "QC", "SK", "YT",
]
selected_provinces = st.sidebar.multiselect(
    "Province/Territory",
    options=provinces,
    default=provinces,
)

# Confidence class filter
confidence_levels = [
    "confirmed_murb",
    "high_confidence_murb",
    "probable_murb",
    "possible_murb",
    "non_murb",
    "insufficient_information",
]
selected_confidence = st.sidebar.multiselect(
    "MURB Confidence Level",
    options=confidence_levels,
    default=confidence_levels[:4],
)

# Area filter
area_range = st.sidebar.slider(
    "Footprint Area (m²)",
    min_value=0,
    max_value=10000,
    value=(200, 5000),
    step=50,
)

# Storey filter
storey_range = st.sidebar.slider(
    "Storeys",
    min_value=1,
    max_value=60,
    value=(2, 30),
)

# --- Main content ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Map", "📈 Distributions", "📋 Data Quality"])

with tab1:
    st.markdown("### National Inventory Summary")

    # Try to load inventory report
    inventory_path = Path("outputs/reports/inventory.json")
    if inventory_path.exists():
        with open(inventory_path) as f:
            inventory = json.load(f)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Files", inventory["total_files"])
        col2.metric("Total Records", f"{inventory['total_records']:,}")
        col3.metric("Total Size", f"{inventory['total_size_mb']:.0f} MB")
        col4.metric("Provinces", len(set(f["province_territory"] for f in inventory["files"])))

        st.markdown("### File Inventory")
        file_data = []
        for f in inventory["files"]:
            completeness = {fc["field_name"]: fc["completeness_pct"]
                          for fc in f["field_completeness"]}
            file_data.append({
                "File": f["file_name"],
                "Province": f["province_territory"],
                "Records": f["total_records"],
                "Size (MB)": f["file_size_mb"],
                "Sources": len(f["source_organizations"]),
                "Type %": completeness.get("type", 0),
                "Floors %": completeness.get("floors", 0),
                "Units %": completeness.get("units", 0),
                "Height %": completeness.get("height", 0),
            })
        st.dataframe(file_data, use_container_width=True)
    else:
        st.info(
            "No inventory data found. Run `murb-geometry inventory` to generate "
            "the data inventory report."
        )

with tab2:
    st.markdown("### Building Footprint Map")
    st.info(
        "Map visualization requires processed GeoParquet data. "
        "This will be available after running the geometry metrics pipeline."
    )

with tab3:
    st.markdown("### Geometry Distributions")
    st.info(
        "Distribution charts will display after geometry metrics are calculated. "
        "Run `murb-geometry metrics` to generate metric data."
    )

with tab4:
    st.markdown("### Data Quality Matrix")
    st.info(
        "Data quality visualization requires the inventory report. "
        "Run `murb-geometry inventory` to generate completeness data."
    )

# --- Footer ---
st.markdown("---")
st.markdown(
    "**Data source:** Statistics Canada Open Database of Buildings v3 "
    "([Open Government Licence - Canada]"
    "(https://open.canada.ca/en/open-government-licence-canada))"
)

