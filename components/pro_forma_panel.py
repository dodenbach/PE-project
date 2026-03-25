"""Panel 3: Pro forma inputs and outputs."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from analysis.pro_forma import (
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
            min_value=5,
            max_value=30,
            value=15,
            key="capture_rate_input",
        ) / 100.0

        revenue_per_stop = st.slider(
            "Revenue per Stop ($)",
            min_value=5,
            max_value=25,
            value=12,
            key="rps_input",
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

        m4, m5, m6 = st.columns(3)
        with m4:
            st.metric("Annual Revenue", f"${pf['annual_gross_revenue']:,.0f}")
        with m5:
            st.metric("Daily Stops", f"{pf['daily_stops']:.0f}")
        with m6:
            irr_display = f"{pf['irr']:.1f}%" if pf["irr"] is not None else "N/A"
            st.metric(f"Unlevered IRR ({hold_years}yr)", irr_display)

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
        st.plotly_chart(cost_fig, use_container_width=True)

        # Sensitivity table
        st.markdown("##### Sensitivity: IRR by Capture Rate x Revenue/Stop")
        st.dataframe(
            pf["sensitivity"],
            use_container_width=True,
        )

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
    st.dataframe(pd.DataFrame(comps_data), use_container_width=True, hide_index=True)

    # Cap rate benchmarks
    col_bench, col_export = st.columns([2, 1])
    with col_bench:
        st.markdown("##### Cap Rate Benchmarks")
        bench_rows = []
        for sector, (low, high) in CAP_RATE_BENCHMARKS.items():
            bench_rows.append({"Sector": sector, "Range": f"{low}% – {high}%"})
        st.dataframe(pd.DataFrame(bench_rows), use_container_width=True, hide_index=True)

    with col_export:
        st.markdown("##### Export")

        # Build CSV export
        export_data = {
            "Metric": [
                "Corridor", "Build Type", "Acres", "Land Cost/Acre",
                "Total Project Cost", "Annual Revenue", "NOI", "Cap Rate",
                f"IRR ({hold_years}yr)", "Daily Stops", "Capture Rate", "Revenue/Stop",
            ],
            "Value": [
                site_context.get("gap", {}).get("mid_lon", "N/A") if site_context else "N/A",
                build_type, acres, f"${land_cost:,.0f}",
                f"${pf['total_project_cost']:,.0f}",
                f"${pf['annual_gross_revenue']:,.0f}",
                f"${pf['noi']:,.0f}",
                f"{pf['cap_rate']:.1f}%",
                f"{pf['irr']:.1f}%" if pf["irr"] else "N/A",
                f"{pf['daily_stops']:.0f}",
                f"{capture_rate:.0%}",
                f"${revenue_per_stop}",
            ],
        }
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False)

        st.download_button(
            label="Download Pro Forma (CSV)",
            data=csv,
            file_name="truck_stop_pro_forma.csv",
            mime="text/csv",
        )

    return pf
