"""Panel 3: Pro forma inputs and outputs."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from engine.pro_forma import (
    calculate_pro_forma, BUILD_TYPES, CAP_RATE_BENCHMARKS, COMPARABLE_TRANSACTIONS,
)


def render_pro_forma(site_context=None):
    """Render the pro forma panel with inputs and outputs."""

    # Defaults from site context if available
    default_land = 5000
    default_aadt = 6000
    if site_context:
        default_land = site_context.get("land_cost", 5000)
        default_aadt = site_context.get("aadt", 6000)

    col_inputs, col_outputs = st.columns([2, 3])

    with col_inputs:
        st.markdown("##### Inputs")

        build_type = st.radio(
            "Build Type",
            list(BUILD_TYPES.keys()),
            key="build_type",
            horizontal=True,
        )
        config = BUILD_TYPES[build_type]
        st.caption(config["description"])

        land_cost = st.number_input(
            "Land Cost ($/acre)",
            min_value=500,
            max_value=500_000,
            value=int(default_land),
            step=500,
            key="land_cost_input",
        )

        acres = st.slider(
            "Acres",
            min_value=config["acres_range"][0],
            max_value=config["acres_range"][1],
            value=config["default_acres"],
            key="acres_input",
        )

        daily_volume = st.number_input(
            "Daily Truck Volume (AADT)",
            min_value=500,
            max_value=30000,
            value=int(default_aadt),
            step=500,
            key="daily_volume_input",
        )

        capture_rate = st.slider(
            "Capture Rate (%)",
            min_value=1,
            max_value=10,
            value=5,
            key="capture_rate_input",
            help="% of passing AADT trucks that stop. Typical: 2-5% independent, 4-8% major chain.",
        ) / 100.0

        revenue_per_stop = st.slider(
            "Net Revenue per Stop ($)",
            min_value=5,
            max_value=25,
            value=12,
            key="rps_input",
            help="Net margin per truck visit (fuel margin + inside sales + parking). Source: NATSO.",
        )

        hold_years = st.slider(
            "Hold Period (years)",
            min_value=3,
            max_value=10,
            value=5,
            key="hold_input",
        )

    # Calculate pro forma
    pf = calculate_pro_forma(
        land_cost_per_acre=land_cost,
        acres=acres,
        build_type=build_type,
        daily_truck_volume=daily_volume,
        capture_rate=capture_rate,
        revenue_per_stop=revenue_per_stop,
        hold_years=hold_years,
    )

    # Store inputs for audit
    pf["_inputs"] = {
        "daily_volume": daily_volume,
        "capture_rate": capture_rate,
        "revenue_per_stop": revenue_per_stop,
        "hold_years": hold_years,
        "land_cost": land_cost,
        "acres": acres,
        "build_type": build_type,
    }

    with col_outputs:
        st.markdown("##### Returns")

        # Key metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Project Cost", f"${pf['total_project_cost']:,.0f}")
        with m2:
            st.metric("Year 1 NOI", f"${pf['noi']:,.0f}",
                       delta=f"{'positive' if pf['noi'] > 0 else 'negative'}")
        with m3:
            cap_display = f"{pf['cap_rate']:.1f}%"
            st.metric("Cap Rate", cap_display)

        if pf.get("capacity_capped"):
            st.warning(
                f"Daily stops capped at {pf['max_daily_trucks']} "
                f"(physical capacity for {build_type}). "
                f"Raw demand: {daily_volume * capture_rate:.0f} trucks/day."
            )

        m4, m5, m6 = st.columns(3)
        with m4:
            st.metric("Annual Revenue", f"${pf['annual_gross_revenue']:,.0f}")
        with m5:
            st.metric("Daily Stops", f"{pf['daily_stops']:.0f}")
        with m6:
            irr_display = f"{pf['irr']:.1f}%" if pf["irr"] is not None else "N/A"
            st.metric(f"Unlevered IRR ({hold_years}yr)", irr_display)

        # Flag unusual cap rates
        if pf["cap_rate"] < 3 or pf["cap_rate"] > 20:
            st.error(f"Unusual cap rate ({pf['cap_rate']:.1f}%) — check inputs")

        st.divider()

        # Cost breakdown
        st.markdown("##### Cost Breakdown")
        cost_fig = go.Figure(go.Waterfall(
            x=["Land", "Construction", "Total"],
            y=[pf["total_land_cost"], pf["build_cost"], 0],
            measure=["absolute", "relative", "total"],
            text=[f"${pf['total_land_cost']:,.0f}", f"${pf['build_cost']:,.0f}",
                  f"${pf['total_project_cost']:,.0f}"],
            textposition="outside",
            textfont=dict(color="#aaa", family="Courier New", size=12),
            connector=dict(line=dict(color="#333")),
            increasing=dict(marker=dict(color="#3B82F6")),
            totals=dict(marker=dict(color="#F59E0B")),
        ))
        cost_fig.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickfont=dict(color="#aaa", family="Courier New")),
            yaxis=dict(showticklabels=False, showgrid=False),
        )
        st.plotly_chart(cost_fig, width="stretch")

        # Sensitivity table
        st.markdown("##### Sensitivity: IRR by Capture Rate x Revenue/Stop")
        st.dataframe(pf["sensitivity"], width="stretch")

    # Comparable transactions
    st.divider()
    st.markdown("##### Market Comparables")
    comps_data = []
    for comp in COMPARABLE_TRANSACTIONS:
        comps_data.append({
            "Property": comp["property"],
            "Year": comp["year"],
            "Sale Price": f"${comp['price']:,.0f}",
            "NOI": f"${comp['noi']:,.0f}",
            "Cap Rate": f"{comp['cap_rate']}%",
            "Acres": comp["acres"],
            "Source": comp["source"],
        })
    st.dataframe(pd.DataFrame(comps_data), width="stretch", hide_index=True)
    st.caption(
        "Source: Peakstone/Alterra $490M portfolio, JP Morgan $95.2M portfolio, "
        "Blackstone $189M loan (2024-2025)"
    )

    # Cap rate benchmarks
    col_bench, col_export = st.columns([2, 1])
    with col_bench:
        st.markdown("##### Cap Rate Benchmarks")
        bench_rows = []
        for sector, (low, high) in CAP_RATE_BENCHMARKS.items():
            bench_rows.append({"Sector": sector, "Range": f"{low}% - {high}%"})
        st.dataframe(pd.DataFrame(bench_rows), width="stretch", hide_index=True)

    with col_export:
        st.markdown("##### Export for deal memo")

        # Build CSV export
        corridor_info = ""
        if site_context:
            gap = site_context.get("gap")
            if gap is not None:
                corridor_info = f"({gap.get('mid_lat', ''):.4f}, {gap.get('mid_lon', ''):.4f})"

        export_data = {
            "Metric": [
                "Location", "Build Type", "Acres", "Land Cost/Acre",
                "Total Project Cost", "Annual Revenue", "Annual OpEx",
                "NOI", "Cap Rate", f"IRR ({hold_years}yr)",
                "Daily Stops", "Capture Rate", "Revenue/Stop",
                "AADT Source", "Land Cost Source",
            ],
            "Value": [
                corridor_info or "N/A",
                build_type, acres, f"${land_cost:,.0f}",
                f"${pf['total_project_cost']:,.0f}",
                f"${pf['annual_gross_revenue']:,.0f}",
                f"${pf['annual_opex']:,.0f}",
                f"${pf['noi']:,.0f}",
                f"{pf['cap_rate']:.1f}%",
                f"{pf['irr']:.1f}%" if pf["irr"] else "N/A",
                f"{pf['daily_stops']:.0f}",
                f"{capture_rate:.0%}",
                f"${revenue_per_stop}",
                "FHWA Highway Statistics, Freight Analysis Framework",
                "USDA NASS Land Values 2023 Summary",
            ],
        }
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False)

        st.download_button(
            label="Export Pro Forma (CSV) — for deal memo",
            data=csv,
            file_name="truck_stop_pro_forma.csv",
            mime="text/csv",
        )

    # Source citations
    st.divider()
    st.caption("AADT values: Source: FHWA Highway Statistics, Freight Analysis Framework")
    st.caption("Land cost: Source: USDA NASS Land Values 2023 Summary")
    st.caption("Construction costs: Source: RSMeans Construction Cost Indices")
    st.caption(
        "Estimates based on FHWA HPMS traffic data, USDA land value surveys, "
        "and RSMeans construction cost indices. For illustrative purposes."
    )

    return pf
