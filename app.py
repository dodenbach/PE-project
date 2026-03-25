"""Truck Stop Site Screener — main Streamlit entrypoint."""

import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    layout="wide",
    page_title="Truck Stop Screener",
    page_icon="\U0001F69B",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""<style>
    .main { background: #0A0A0A; }
    section[data-testid="stSidebar"] { background: #111111; }
    .metric-label, .stMetric label { font-family: 'Courier New', monospace; }
    .stSelectbox label, .stRadio label { color: #F59E0B !important; }
    div[data-testid="stMetricValue"] { font-family: 'Courier New', monospace; }
    .stTabs [data-baseweb="tab"] { font-family: 'Courier New', monospace; }
    .stDataFrame { font-family: 'Courier New', monospace; font-size: 12px; }
</style>""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style="border-bottom: 1px solid #333; padding-bottom: 12px; margin-bottom: 20px;">
    <h1 style="margin: 0; font-family: 'Courier New', monospace; color: #F59E0B;">
        TRUCK STOP SCREENER
    </h1>
    <p style="color: #888; margin: 4px 0 0 0; font-family: 'Courier New', monospace; font-size: 14px;">
        <em>"HOS regulations create mandatory demand. This tool identifies where supply is thin."</em>
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### Corridor Selection")
    corridor = st.selectbox(
        "Interstate",
        ["I-80", "I-40", "I-10", "I-70", "I-90"],
        index=0,
    )
    gap_threshold = st.slider(
        "Gap Threshold (miles)",
        min_value=40,
        max_value=200,
        value=80,
        step=10,
        help="Minimum distance between stops to qualify as a gap zone.",
    )

    st.divider()
    st.markdown(
        "<p style='font-size: 11px; color: #555; font-family: Courier New;'>"
        "Estimates based on FHWA HPMS traffic data, USDA land value surveys, "
        "and RSMeans construction cost indices. For illustrative purposes.</p>",
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Fetching route geometry...")
def load_route(corridor):
    from data.fetch_routes import fetch_route
    return fetch_route(corridor)


@st.cache_data(show_spinner="Fetching truck stops...")
def load_stops(corridor):
    from data.fetch_stops import fetch_stops
    return fetch_stops(corridor)


@st.cache_data(show_spinner="Running gap analysis...")
def run_gap_analysis(corridor, gap_threshold):
    from analysis.hos_gaps import find_gap_zones
    route_df = load_route(corridor)
    stops_df = load_stops(corridor)
    gaps_df = find_gap_zones(route_df, stops_df, gap_threshold)
    return gaps_df


# Load data
try:
    route_df = load_route(corridor)
    stops_df = load_stops(corridor)
    gaps_df = run_gap_analysis(corridor, gap_threshold)

    # Summary stats in sidebar
    with st.sidebar:
        st.markdown("### Quick Stats")
        st.metric("Route Points", f"{len(route_df):,}")
        st.metric("Truck Stops Found", f"{len(stops_df):,}")
        st.metric("Gap Zones", f"{len(gaps_df):,}")
        if not gaps_df.empty:
            st.metric("Largest Gap", f"{gaps_df['gap_miles'].max():.0f} mi")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("The Overpass API may be rate-limited. Try again in a few seconds.")
    st.stop()


# Three tabs
tab1, tab2, tab3 = st.tabs(["Corridor Explorer", "Site Scoring", "Pro Forma"])

with tab1:
    from data.fetch_routes import get_corridor_center
    from components.corridor_map import build_corridor_map

    center = get_corridor_center(corridor)
    m = build_corridor_map(route_df, stops_df, gaps_df, center=center, zoom=5)
    st_folium(m, width=None, height=600, returned_objects=[])

    if not gaps_df.empty:
        st.markdown("##### Gap Zones Summary")
        display_df = gaps_df[["gap_miles", "severity", "nearest_stop_before", "nearest_stop_after",
                               "mid_lat", "mid_lon"]].copy()
        display_df.columns = ["Gap (mi)", "Severity", "Stop Before", "Stop After", "Lat", "Lon"]
        display_df.index = range(1, len(display_df) + 1)
        display_df.index.name = "#"
        st.dataframe(display_df, use_container_width=True)
    else:
        st.success("No significant gaps found on this corridor at the current threshold.")


with tab2:
    from components.site_scoring import render_site_scoring
    site_context = render_site_scoring(gaps_df, corridor)

with tab3:
    from components.pro_forma_panel import render_pro_forma
    render_pro_forma(site_context=site_context)
