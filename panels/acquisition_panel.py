"""Panel 4: Acquisition Screener — identify independent truck stops as buyout targets."""

import streamlit as st
import pandas as pd
import numpy as np

from engine.acquisition import (
    get_independents, score_acquisition_target, compute_unit_economics,
    acquisition_price_table, count_rollup_targets,
)
from sources.fetch_aadt import get_aadt_at_lon
from sources.land_costs import get_land_cost, get_state_at_lon, classify_location


def render_acquisition_screener(
    stops_df: pd.DataFrame,
    gaps_df: pd.DataFrame,
    corridor: str,
):
    """Render the acquisition screener panel."""

    # Thesis callout
    st.markdown(
        '<div style="background: rgba(245,158,11,0.08); border: 1px solid #F59E0B; '
        'border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; '
        'font-family: Courier New, monospace; font-size: 13px; color: #ccc;">'
        '~60% of US truck stop establishments are single-store independents (NATSO). '
        'Fragmented ownership + regulatory demand floor = classic roll-up setup. '
        'Entry multiples: 4&ndash;6x EBITDA. Institutional IOS comps trading at '
        '5&ndash;6% cap rate (Blackstone, JP Morgan, Peakstone, 2024&ndash;2025).'
        '<br><span style="color: #777; font-size: 11px;">'
        'Source: Peakstone/Alterra $490M portfolio, JP Morgan $95.2M portfolio, '
        'Blackstone $189M loan (2024&ndash;2025)</span></div>',
        unsafe_allow_html=True,
    )

    # Get independents
    independents = get_independents(stops_df)

    if independents.empty:
        st.info("No independent truck stops found on this corridor.")
        return

    # Score each independent
    scored_rows = []
    for _, stop in independents.iterrows():
        aadt = get_aadt_at_lon(corridor, stop["lon"])
        state = get_state_at_lon(corridor, stop["lon"])
        classification = classify_location(stop["lon"], corridor)
        land_cost = get_land_cost(state, classification)

        score_data = score_acquisition_target(
            stop["lat"], stop["lon"], gaps_df, aadt, land_cost,
        )
        econ = compute_unit_economics(aadt)
        rollup_count = count_rollup_targets(
            stop["lat"], stop["lon"], independents,
        )

        scored_rows.append({
            "name": stop["name"],
            "operator": stop["operator"],
            "lat": stop["lat"],
            "lon": stop["lon"],
            "state": state,
            "location_score": score_data["location_score"],
            "near_gap": score_data["near_gap"],
            "aadt": aadt,
            "land_cost": land_cost,
            "daily_captures": econ["daily_captures"],
            "annual_revenue": econ["annual_gross_revenue"],
            "ebitda": econ["ebitda"],
            "rollup_count": rollup_count,
            "gap_pts": score_data["gap_proximity_score"],
            "aadt_pts": score_data["aadt_score"],
            "land_pts": score_data["land_score"],
        })

    scored_df = pd.DataFrame(scored_rows).sort_values(
        "location_score", ascending=False,
    ).reset_index(drop=True)

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Independent Stops", len(scored_df))
    with c2:
        st.metric("Avg Location Score", f"{scored_df['location_score'].mean():.0f}/100")
    with c3:
        st.metric("Near Gap Zones", f"{scored_df['near_gap'].sum()}")
    with c4:
        avg_ebitda = scored_df["ebitda"].mean()
        st.metric("Avg Est. EBITDA", f"${avg_ebitda:,.0f}")

    st.divider()

    # Ranked table
    st.markdown("##### Acquisition Targets — Ranked by Location Score")

    display_df = scored_df[["name", "operator", "state", "location_score",
                             "near_gap", "aadt", "ebitda"]].copy()
    display_df.columns = ["Name", "Operator", "State", "Score", "Near Gap", "AADT", "Est. EBITDA"]
    display_df["Est. EBITDA"] = display_df["Est. EBITDA"].apply(lambda x: f"${x:,.0f}")
    display_df["AADT"] = display_df["AADT"].apply(lambda x: f"{x:,}")
    display_df.index = range(1, len(display_df) + 1)

    # Badge top 3
    badges = []
    for i in range(len(display_df)):
        badges.append("Priority Target" if i < 3 else "")
    display_df.insert(0, "Status", badges)

    st.dataframe(display_df, width="stretch", hide_index=True, height=400)

    st.caption(
        "Source: Stop locations from OpenStreetMap/Overpass API. EBITDA = AADT x 8% capture x "
        "$14/stop x 365 x 28% margin. Source: NATSO Independent Operator Industry Average."
    )

    st.divider()

    # Expandable detail for top targets
    st.markdown("##### Target Detail")

    # Let user pick a target
    target_options = [
        f"{'Priority Target — ' if i < 3 else ''}{row['name']} (Score: {row['location_score']})"
        for i, row in scored_df.iterrows()
    ]
    selected_target = st.selectbox(
        "Select Target",
        range(len(target_options)),
        format_func=lambda i: target_options[i],
        key="acq_target_selector",
    )

    target = scored_df.iloc[selected_target]

    col_econ, col_price = st.columns(2)

    with col_econ:
        st.markdown("##### Unit Economics")
        st.markdown(f"""
| Metric | Value |
|---|---|
| **Corridor AADT** | {target['aadt']:,} trucks/day |
| **Capture Rate** | 8% (conservative independent) |
| **Daily Captures** | {target['daily_captures']:.0f} trucks |
| **Revenue/Stop** | $14 blended avg |
| **Annual Revenue** | ${target['annual_revenue']:,.0f} |
| **EBITDA Margin** | 28% |
| **EBITDA** | ${target['ebitda']:,.0f} |
        """)

        st.caption(
            "$14 blended average = parking fee + fuel margin per stop. Source: NATSO industry data."
        )
        st.caption(
            "28% EBITDA margin = NATSO independent operator industry average. "
            "Actual margins vary by fuel volume and service mix."
        )

    with col_price:
        st.markdown("##### Acquisition Price Table")
        price_df = acquisition_price_table(target["ebitda"])
        st.dataframe(price_df, width="stretch", hide_index=True)

        st.caption(
            "Source: Entry multiples based on independent truck stop M&A comps. "
            "Institutional IOS comps at 5-6% cap rate (Peakstone/Alterra $490M, "
            "JP Morgan $95.2M, Blackstone $189M, 2024-2025)."
        )

    # Score breakdown
    st.markdown("##### Location Score Breakdown")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        label = "Within 20mi of gap zone" if target["near_gap"] else "Not near gap zone"
        st.metric("Gap Proximity (40 pts max)", f"{target['gap_pts']:.0f}", delta=label)
    with col_s2:
        st.metric("Traffic / AADT (35 pts max)", f"{target['aadt_pts']:.0f}")
    with col_s3:
        st.metric("Land Cost Inverse (25 pts max)", f"{target['land_pts']:.0f}")

    st.caption("Source: Gap analysis from FMCSA HOS regulations (49 CFR Part 395). "
               "AADT from FHWA Highway Statistics, Freight Analysis Framework. "
               "Land cost from USDA NASS Land Values 2023 Summary.")

    # Roll-up TAM
    st.divider()
    rollup = target["rollup_count"]
    st.markdown(
        f'<div style="background: rgba(245,158,11,0.08); border: 1px solid #F59E0B; '
        f'border-radius: 8px; padding: 12px 16px; font-family: Courier New; font-size: 14px; '
        f'color: #F59E0B;">'
        f'<b>{rollup}</b> independent operators within 300-mile radius &mdash; '
        f'platform roll-up potential</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Export
    st.markdown("##### Export for deal memo")
    export_rows = []
    for _, row in scored_df.iterrows():
        export_rows.append({
            "Name": row["name"],
            "Operator": row["operator"],
            "State": row["state"],
            "Location Score": row["location_score"],
            "Near Gap Zone": row["near_gap"],
            "AADT": row["aadt"],
            "Daily Captures": row["daily_captures"],
            "Annual Revenue": row["annual_revenue"],
            "EBITDA": row["ebitda"],
            "Price @ 4x": row["ebitda"] * 4,
            "Price @ 5x": row["ebitda"] * 5,
            "Price @ 6x": row["ebitda"] * 6,
            "Rollup Targets (300mi)": row["rollup_count"],
            "Lat": row["lat"],
            "Lon": row["lon"],
        })
    export_df = pd.DataFrame(export_rows)
    csv = export_df.to_csv(index=False)

    st.download_button(
        label="Export Acquisition Targets (CSV) — for deal memo",
        data=csv,
        file_name=f"acquisition_targets_{corridor}.csv",
        mime="text/csv",
        key="acq_export",
    )
