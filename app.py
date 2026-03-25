"""Truck Stop Site Screener — main Streamlit entrypoint."""

import streamlit as st
import pandas as pd

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
<div style="border-bottom: 1px solid #333; padding-bottom: 12px; margin-bottom: 8px;">
    <h1 style="margin: 0; font-family: 'Courier New', monospace; color: #F59E0B;">
        TRUCK STOP SCREENER
    </h1>
</div>
""", unsafe_allow_html=True)

# Updated thesis statement (Addition 1)
st.markdown(
    '<div style="background: rgba(245,158,11,0.06); border: 1px solid #F59E0B; '
    'border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; '
    'font-family: Courier New, monospace; font-size: 13px; color: #ccc;">'
    'Truck parking is the <b style="color:#F59E0B;">#2 critical issue</b> in US trucking '
    '(ATRI, 2024). There is <b style="color:#F59E0B;">1 parking space for every 11 drivers</b> '
    'on the road. HOS regulations create mandatory demand &mdash; this tool identifies where '
    'supply is thinnest and who to buy.'
    '<br><span style="color: #666; font-size: 11px;">'
    'Source: American Transportation Research Institute (ATRI) Critical Issues Report, 2024</span>'
    '</div>',
    unsafe_allow_html=True,
)

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


@st.cache_data(show_spinner="Fetching route geometry...", ttl=3600)
def load_route(corridor):
    try:
        from sources.fetch_routes import fetch_route
        return fetch_route(corridor)
    except Exception as e:
        st.warning(f"Could not fetch route from Overpass API: {e}")
        return pd.DataFrame(columns=["lat", "lon", "sequence"])


@st.cache_data(show_spinner="Fetching truck stops...", ttl=3600)
def load_stops(corridor):
    try:
        from sources.fetch_stops import fetch_stops
        return fetch_stops(corridor)
    except Exception as e:
        st.warning(f"Could not fetch stops from Overpass API: {e}")
        return pd.DataFrame(columns=["name", "operator", "lat", "lon", "is_major"])


def run_gap_analysis(route_df, stops_df, gap_threshold):
    from engine.hos_gaps import find_gap_zones
    return find_gap_zones(route_df, stops_df, gap_threshold)


# Load data
route_df = load_route(corridor)
stops_df = load_stops(corridor)
gaps_df = run_gap_analysis(route_df, stops_df, gap_threshold)

# Summary stats in sidebar
with st.sidebar:
    st.markdown("### Quick Stats")
    st.metric("Route Points", f"{len(route_df):,}")
    st.metric("Truck Stops Found", f"{len(stops_df):,}")
    st.metric("Gap Zones", f"{len(gaps_df):,}")
    if not gaps_df.empty:
        st.metric("Largest Gap", f"{gaps_df['gap_miles'].max():.0f} mi")

    # Count independents for sidebar
    from engine.acquisition import get_independents
    independents = get_independents(stops_df)
    st.metric("Independent Stops", f"{len(independents):,}")

if route_df.empty:
    st.warning(
        "The Overpass API did not return route data. This can happen due to rate limiting "
        "or network issues from the cloud host. Try refreshing in a few seconds."
    )

# Four tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Corridor Explorer",
    "Site Scoring",
    "Pro Forma",
    "Acquisition Screener",
])

# Track pro forma results for audit
pf_result = None

with tab1:
    from sources.fetch_routes import get_corridor_center
    from panels.corridor_map import build_corridor_map

    center = get_corridor_center(corridor)
    m = build_corridor_map(route_df, stops_df, gaps_df, center=center, zoom=5)

    try:
        from streamlit_folium import st_folium
        st_folium(m, width=None, height=600)
    except Exception:
        st.components.v1.html(m._repr_html_(), height=600)

    if not gaps_df.empty:
        st.markdown("##### Gap Zones Summary")
        display_df = gaps_df[["gap_miles", "severity", "nearest_stop_before", "nearest_stop_after",
                               "mid_lat", "mid_lon"]].copy()
        display_df.columns = ["Gap (mi)", "Severity", "Stop Before", "Stop After", "Lat", "Lon"]
        display_df.index = range(1, len(display_df) + 1)
        display_df.index.name = "#"
        st.dataframe(display_df, width="stretch")
        st.caption("Source: Gap analysis based on FMCSA Hours of Service regulations (49 CFR Part 395). "
                   "Stop locations from OpenStreetMap/Overpass API.")
    else:
        st.success("No significant gaps found on this corridor at the current threshold.")


with tab2:
    from panels.site_scoring import render_site_scoring
    site_context = render_site_scoring(gaps_df, corridor)

with tab3:
    from panels.pro_forma_panel import render_pro_forma
    pf_result = render_pro_forma(site_context=site_context)

with tab4:
    from panels.acquisition_panel import render_acquisition_screener
    render_acquisition_screener(stops_df, gaps_df, corridor)


# Data Audit in sidebar (Addition 3)
with st.sidebar:
    from panels.data_audit import render_data_audit

    pf_inputs = None
    if pf_result and isinstance(pf_result, dict):
        pf_inputs = pf_result.get("_inputs")

    # Build acquisition data for audit
    acq_data = None
    if not independents.empty:
        from sources.fetch_aadt import get_aadt_at_lon
        from engine.acquisition import compute_unit_economics
        acq_data = []
        for _, stop in independents.head(5).iterrows():
            aadt = get_aadt_at_lon(corridor, stop["lon"])
            econ = compute_unit_economics(aadt)
            acq_data.append({
                "name": stop["name"],
                "aadt": aadt,
                "daily_captures": econ["daily_captures"],
                "ebitda": econ["ebitda"],
            })

    render_data_audit(
        corridor=corridor,
        route_df=route_df,
        stops_df=stops_df,
        gaps_df=gaps_df,
        gap_threshold=gap_threshold,
        pf_result=pf_result if isinstance(pf_result, dict) else None,
        pf_inputs=pf_inputs,
        acquisition_data=acq_data,
    )
