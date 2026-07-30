"""Canadian MURB Geometry Analysis — Streamlit Visualization Application.

Reads persisted pipeline outputs (GeoParquet, manifests, CSVs).
No recalculation — all data comes from validated analytical outputs.

Launch with: streamlit run app/streamlit_app.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from murb_geometry.datastore import subset_path

st.set_page_config(
    page_title="Canadian MURB Geometry Analysis",
    page_icon="🏢",
    layout="wide",
)

# --- Data Loading ---
PRECISION_PATH = subset_path("precision")
TIERED_PATH = subset_path("tiered")
MANIFEST_PATH = Path("outputs/reports/run_manifest.json")
INVENTORY_PATH = Path("outputs/reports/inventory.json")
SENSITIVITY_PATH = Path("outputs/reports/pathway_sensitivity.csv")
CLASSIFICATION_PATH = Path("outputs/reports/classification_summary.csv")


@st.cache_data
def load_parquet(path: Path) -> pd.DataFrame:
    """Load GeoParquet as DataFrame (drop geometry for speed)."""
    if not path.exists():
        return pd.DataFrame()
    import geopandas as gpd

    gdf = gpd.read_parquet(path)
    return pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))


@st.cache_data
def load_json(path: Path) -> dict:
    """Load JSON file."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    """Load CSV file."""
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# Load data
precision_df = load_parquet(PRECISION_PATH)
tiered_df = load_parquet(TIERED_PATH)
manifest = load_json(MANIFEST_PATH)
inventory = load_json(INVENTORY_PATH)
sensitivity_df = load_csv(SENSITIVITY_PATH)
classification_df = load_csv(CLASSIFICATION_PATH)

# --- Header ---
st.title("🏢 Canadian MURB Geometry Analysis")
st.caption("Statistics Canada Open Database of Buildings v3 — Multi-Pathway Visualization")

# --- Sidebar: Filters ---
st.sidebar.header("Filters")

# Pathway selection
pathway = st.sidebar.radio(
    "Classification Pathway",
    options=["Precision", "Tiered"],
    index=0,
    help="Precision: confirmed + high-confidence only. Tiered: includes probable + possible.",
)
df = precision_df if pathway == "Precision" else tiered_df

if df.empty:
    st.error("No processed data found. Run `murb-geometry run-all` first.")
    st.stop()

# Province filter
available_provinces = sorted(df["_province"].dropna().unique()) if "_province" in df.columns else []
selected_provinces = st.sidebar.multiselect(
    "Province/Territory",
    options=available_provinces,
    default=available_provinces,
)

# Confidence filter
if "confidence_level" in df.columns:
    available_levels = sorted(df["confidence_level"].dropna().unique())
    selected_confidence = st.sidebar.multiselect(
        "Confidence Level",
        options=available_levels,
        default=available_levels,
    )
else:
    selected_confidence = []

# Area filter
if "footprint_area_m2" in df.columns:
    area_max = min(float(df["footprint_area_m2"].max()), 15000.0)
    area_range = st.sidebar.slider(
        "Footprint Area (m²)",
        min_value=0.0,
        max_value=area_max,
        value=(0.0, area_max),
        step=50.0,
    )
else:
    area_range = (0.0, 99999.0)

# Apply filters
filtered = df.copy()
if selected_provinces and "_province" in filtered.columns:
    filtered = filtered[filtered["_province"].isin(selected_provinces)]
if selected_confidence and "confidence_level" in filtered.columns:
    filtered = filtered[filtered["confidence_level"].isin(selected_confidence)]
if "footprint_area_m2" in filtered.columns:
    filtered = filtered[
        (filtered["footprint_area_m2"] >= area_range[0])
        & (filtered["footprint_area_m2"] <= area_range[1])
    ]

st.sidebar.markdown("---")
st.sidebar.metric("Filtered Buildings", f"{len(filtered):,}")
st.sidebar.metric("Total in Pathway", f"{len(df):,}")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "📈 Distributions", "🔬 Classification", "📋 Data Quality", "🏗️ Building Data"]
)

# === TAB 1: Overview ===
with tab1:
    st.markdown(f"### {pathway} Pathway — {len(filtered):,} Buildings")

    col1, col2, col3, col4 = st.columns(4)
    if "footprint_area_m2" in filtered.columns:
        col1.metric("Median Area (m²)", f"{filtered['footprint_area_m2'].median():.0f}")
    if "aspect_ratio" in filtered.columns:
        col2.metric("Median Aspect Ratio", f"{filtered['aspect_ratio'].median():.2f}")
    if "floors_numeric" in filtered.columns:
        valid_floors = filtered["floors_numeric"].dropna()
        col3.metric(
            "Median Storeys", f"{valid_floors.median():.0f}" if len(valid_floors) > 0 else "N/A"
        )
    if "_province" in filtered.columns:
        col4.metric("Provinces", filtered["_province"].nunique())

    # Province breakdown
    if "_province" in filtered.columns:
        st.markdown("#### Buildings by Province")
        prov_counts = filtered["_province"].value_counts().reset_index()
        prov_counts.columns = ["Province", "Buildings"]
        fig = px.bar(
            prov_counts,
            x="Province",
            y="Buildings",
            color="Buildings",
            color_continuous_scale="Blues",
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Pathway sensitivity
    if not sensitivity_df.empty:
        st.markdown("#### Pathway Sensitivity Comparison")
        st.dataframe(sensitivity_df, use_container_width=True)

# === TAB 2: Distributions ===
with tab2:
    st.markdown("### Geometry Distributions")

    metric_col = st.selectbox(
        "Select Metric",
        options=[
            c
            for c in [
                "footprint_area_m2",
                "aspect_ratio",
                "compactness",
                "rectangularity",
                "convexity",
                "mrr_length_m",
                "mrr_width_m",
                "perimeter_m",
                "orientation_deg",
                "floors_numeric",
                "units_numeric",
            ]
            if c in filtered.columns
        ],
    )

    if metric_col:
        values = filtered[metric_col].dropna()
        if len(values) > 0:
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("N", f"{len(values):,}")
            col2.metric("Median", f"{values.median():.2f}")
            col3.metric("Mean", f"{values.mean():.2f}")
            col4.metric("P25", f"{values.quantile(0.25):.2f}")
            col5.metric("P75", f"{values.quantile(0.75):.2f}")

            fig = px.histogram(
                filtered,
                x=metric_col,
                nbins=50,
                color="_province" if "_province" in filtered.columns else None,
                title=f"Distribution of {metric_col}",
                marginal="box",
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

            if "_province" in filtered.columns and filtered["_province"].nunique() > 1:
                fig2 = px.box(
                    filtered, x="_province", y=metric_col, title=f"{metric_col} by Province"
                )
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

# === TAB 3: Classification ===
with tab3:
    st.markdown("### Classification Analysis")

    if "confidence_level" in filtered.columns:
        conf_counts = filtered["confidence_level"].value_counts().reset_index()
        conf_counts.columns = ["Confidence Level", "Count"]
        fig = px.pie(
            conf_counts,
            values="Count",
            names="Confidence Level",
            title="Classification Confidence Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    if "rule_id" in filtered.columns:
        st.markdown("#### Classification Rules Applied")
        rule_counts = filtered["rule_id"].value_counts().reset_index()
        rule_counts.columns = ["Rule", "Count"]
        st.dataframe(rule_counts, use_container_width=True)

    if not classification_df.empty:
        st.markdown("#### Full Classification Summary (All Provinces)")
        st.dataframe(classification_df, use_container_width=True)

# === TAB 4: Data Quality ===
with tab4:
    st.markdown("### Data Quality")

    if inventory:
        st.markdown("#### File Inventory")
        file_data = []
        for f in inventory.get("files", []):
            completeness = {
                fc["field_name"]: fc["completeness_pct"] for fc in f["field_completeness"]
            }
            file_data.append(
                {
                    "File": f["file_name"],
                    "Province": f["province_territory"],
                    "Records": f["total_records"],
                    "Size (MB)": round(f["file_size_mb"], 1),
                    "Sources": len(f["source_organizations"]),
                    "Type %": round(completeness.get("type", 0), 1),
                    "Floors %": round(completeness.get("floors", 0), 1),
                    "Units %": round(completeness.get("units", 0), 1),
                    "Height %": round(completeness.get("height", 0), 1),
                }
            )
        st.dataframe(file_data, use_container_width=True)

        if file_data:
            heatmap_df = pd.DataFrame(file_data)
            fields = ["Type %", "Floors %", "Units %", "Height %"]
            fig = px.imshow(
                heatmap_df[fields].values,
                x=fields,
                y=heatmap_df["Province"].tolist(),
                color_continuous_scale="RdYlGn",
                aspect="auto",
                title="Field Completeness by Province (%)",
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run `murb-geometry inventory` to generate inventory data.")

    # Missingness in filtered data
    st.markdown("#### Field Completeness in Filtered Buildings")
    if not filtered.empty:
        completeness_data = []
        for col in filtered.columns:
            non_null = filtered[col].notna().sum()
            completeness_data.append(
                {
                    "Field": col,
                    "Non-Missing": non_null,
                    "Missing": len(filtered) - non_null,
                    "Completeness %": round(100 * non_null / len(filtered), 1),
                }
            )
        comp_df = pd.DataFrame(completeness_data).sort_values("Completeness %")
        st.dataframe(comp_df, use_container_width=True, height=400)

# === TAB 5: Building Data ===
with tab5:
    st.markdown("### Building-Level Data")
    st.caption(f"Showing {len(filtered):,} buildings (filtered)")

    display_cols = [
        c
        for c in [
            "_province",
            "confidence_level",
            "rule_id",
            "type_normalized",
            "units_numeric",
            "floors_numeric",
            "footprint_area_m2",
            "aspect_ratio",
            "compactness",
            "rectangularity",
            "convexity",
            "mrr_length_m",
            "mrr_width_m",
            "orientation_deg",
        ]
        if c in filtered.columns
    ]

    selected_cols = st.multiselect(
        "Display Columns",
        options=[c for c in filtered.columns if c != "geometry"],
        default=display_cols,
    )

    if selected_cols:
        st.dataframe(filtered[selected_cols].head(1000), use_container_width=True, height=500)
        if len(filtered) > 1000:
            st.caption(
                f"Showing first 1,000 of {len(filtered):,} records. Download full data below."
            )

    st.download_button(
        "📥 Download Filtered Data (CSV)",
        data=filtered[selected_cols].to_csv(index=False) if selected_cols else "",
        file_name=f"murb_{pathway.lower()}_filtered.csv",
        mime="text/csv",
    )

# --- Footer ---
st.markdown("---")
col1, col2 = st.columns(2)
col1.markdown(
    "**Source:** Statistics Canada Open Database of Buildings v3 "
    "([Open Government Licence](https://open.canada.ca/en/open-government-licence-canada))"
)
if manifest:
    col2.markdown(f"**Pipeline run:** {manifest.get('started_at', 'N/A')[:19]}")
