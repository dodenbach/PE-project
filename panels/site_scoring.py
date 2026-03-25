"""Panel 2: Site scoring breakdown for a selected gap zone."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from engine.opportunity_score import score_gap_zone, score_label, score_color
from sources.fetch_aadt import get_aadt_at_lon
from sources.land_costs import get_land_cost, get_state_at_lon, classify_location


def render_site_scoring(gaps_df: pd.DataFrame, corridor: str):
    """Render the site scoring panel for a selected gap zone."""
    if gaps_df.empty:
        st.info("No gap zones found on this corridor. All segments are well-served.")
        return None

    # Gap zone selector
    gap_options = []
    for i, gap in gaps_df.iterrows():
        label = (f"Gap #{i+1}: {gap['gap_miles']}mi — "
                 f"{gap.get('nearest_stop_before', '?')} to {gap.get('nearest_stop_after', '?')} "
                 f"({gap['severity'].upper()})")
        gap_options.append(label)

    selected_idx = st.selectbox(
        "Select Gap Zone",
        range(len(gap_options)),
        format_func=lambda i: gap_options[i],
        key="gap_selector",
    )

    gap = gaps_df.iloc[selected_idx]

    # Get contextual data
    mid_lon = gap["mid_lon"]
    state = get_state_at_lon(corridor, mid_lon)
    classification = classify_location(mid_lon, corridor)
    aadt = get_aadt_at_lon(corridor, mid_lon)
    land_cost = get_land_cost(state, classification)

    # Calculate score
    score_data = score_gap_zone(gap["gap_miles"], aadt, land_cost)
    total_score = score_data["total_score"]
    color = score_color(total_score)
    label = score_label(total_score)

    # Score header
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Opportunity Score", f"{total_score:.0f}/100")
    with col2:
        st.metric("Verdict", label)
    with col3:
        st.metric("Gap Severity", gap["severity"].upper())

    st.divider()

    # Score breakdown chart
    col_chart, col_details = st.columns([3, 2])

    with col_chart:
        st.markdown("##### Score Breakdown")
        fig = go.Figure()

        categories = ["Gap Severity", "Traffic (AADT)", "Land Cost"]
        scores = [score_data["gap_score"], score_data["aadt_score"], score_data["land_score"]]
        weights = [score_data["gap_weight"], score_data["aadt_weight"], score_data["land_weight"]]
        weighted = [s * w for s, w in zip(scores, weights)]
        colors = ["#EF4444", "#3B82F6", "#22C55E"]

        fig.add_trace(go.Bar(
            y=categories,
            x=weighted,
            orientation="h",
            marker_color=colors,
            text=[f"{s:.0f} x {w:.0%} = {ws:.1f}" for s, w, ws in zip(scores, weights, weighted)],
            textposition="inside",
            textfont=dict(color="white", size=13, family="Courier New"),
        ))

        fig.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(range=[0, 50], showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(color="#aaa", family="Courier New", size=13)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, width="stretch")

    with col_details:
        st.markdown("##### Site Details")
        st.markdown(f"""
| Metric | Value |
|---|---|
| **State** | {state} |
| **Classification** | {classification.title()} |
| **Gap Distance** | {gap['gap_miles']} miles |
| **Truck AADT** | {aadt:,}/day |
| **Land Cost** | ${land_cost:,.0f}/acre |
| **Nearest Before** | {gap.get('nearest_stop_before', 'N/A')} |
| **Nearest After** | {gap.get('nearest_stop_after', 'N/A')} |
        """)

    st.divider()

    # Source citations
    st.caption(
        f"Verify zoning with {state} DOT — most interstate exits are zoned I-2 or C-3 commercial."
    )
    st.caption("AADT: Source: FHWA Highway Statistics, Freight Analysis Framework")
    st.caption("Land cost: Source: USDA NASS Land Values 2023 Summary")
    st.caption("Gap threshold: Source: FMCSA Hours of Service regulations (49 CFR Part 395)")

    return {
        "gap": gap,
        "state": state,
        "classification": classification,
        "aadt": aadt,
        "land_cost": land_cost,
        "score_data": score_data,
    }
