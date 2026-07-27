"""Canadian MURB Geometry Analysis — Streamlit Visualization Application.

Launch with: streamlit run app/streamlit_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Canadian MURB Geometry Analysis",
    page_icon="🏢",
    layout="wide",
)

st.title("Canadian MURB Geometry Analysis")
st.subheader("Statistics Canada Open Database of Buildings — Visualization Tool")

st.info(
    """
    **Status: Phase 0 — Repository Initiation**

    This application is under development. The full visualization tool will support:

    - Province and source selection
    - MURB confidence class filtering
    - Interactive map display of building footprints
    - Geometry metric distributions and boxplots
    - Shape classification inspection
    - Archetype selection and comparison
    - Excel report generation
    - Future gbXML export

    See `README.md` and `docs/roadmap.md` for the implementation timeline.
    """
)

st.markdown("---")
st.markdown(
    "**Data source:** Statistics Canada Open Database of Buildings v3 "
    "([Open Government Licence - Canada]"
    "(https://open.canada.ca/en/open-government-licence-canada))"
)
