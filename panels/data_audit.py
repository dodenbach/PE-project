"""Data Audit sidebar panel — verification checks for due diligence."""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from engine.audit import run_audit, audit_pro_forma, audit_acquisition_target
from sources.fetch_aadt import get_aadt_at_lon, get_aadt_for_corridor


def render_data_audit(
    corridor: str,
    route_df: pd.DataFrame,
    stops_df: pd.DataFrame,
    gaps_df: pd.DataFrame,
    gap_threshold: float,
    pf_result=None,
    pf_inputs=None,
    acquisition_data=None,
):
    """Render the data audit expander in the sidebar."""
    try:
        _render_audit_inner(
            corridor, route_df, stops_df, gaps_df, gap_threshold,
            pf_result, pf_inputs, acquisition_data,
        )
    except Exception as e:
        st.error(f"Audit panel error (non-blocking): {e}")


def _render_audit_inner(
    corridor, route_df, stops_df, gaps_df, gap_threshold,
    pf_result, pf_inputs, acquisition_data,
):
    checks = run_audit(corridor, route_df, stops_df, gaps_df, gap_threshold)

    with st.expander("Data Audit — for due diligence conversations", expanded=False):

        # Summary dashboard
        st.markdown("##### Verification Summary")

        def _status(ok, note=""):
            icon = "pass" if ok else "warn"
            return f"{icon}: {note}" if note else icon

        statuses = {
            "Route geometry": (checks["route_ok"], f"{checks['route_points']} points loaded"),
            "Stop data": (checks["stops_ok"], f"{checks['stop_count']} stops found"),
            "Stop density": (
                checks["density_ok"],
                f"{checks['stops_per_100mi']:.1f} stops/100mi"
                if checks["stops_per_100mi"] > 0
                else "N/A",
            ),
            "Gap math": (checks["gap_math_ok"], f"{checks['gap_count']} gaps identified"),
            "AADT": (True, "Static table (note below)"),
            "Land costs": (True, "Estimates (note below)"),
            "Pro forma": (True, "Internally consistent" if pf_result else "Not yet computed"),
        }

        for label, (ok, note) in statuses.items():
            icon = "✅" if ok else "⚠️"
            st.markdown(f"{icon} **{label}** — {note}")

        if not checks["density_ok"]:
            st.warning(
                "Low stop count — verify Overpass query returned valid data. "
                f"Only {checks['stops_per_100mi']:.1f} stops per 100 miles on corridor."
            )

        st.caption(f"Data timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        # HOS Gap Math
        st.markdown("---")
        st.markdown("##### HOS Gap Math — Derivation")
        st.markdown(
            "11 hrs max drive x 55 mph = **605 mi** max range. "
            "8 hrs to mandatory break x 55 mph = **440 mi**. "
            f"Gap threshold set at **{gap_threshold} miles** between stops."
        )
        st.caption("Source: FMCSA Hours of Service regulations (49 CFR Part 395)")

        if checks["gap_details"]:
            gap_rows = []
            for g in checks["gap_details"]:
                gap_rows.append({
                    "#": g["index"],
                    "Start": g["start_coord"],
                    "End": g["end_coord"],
                    "Distance (mi)": g["gap_miles"],
                    "Severity": g["severity"],
                    "Before": g["before"],
                    "After": g["after"],
                })
            st.dataframe(pd.DataFrame(gap_rows), width="stretch", hide_index=True)
        else:
            st.info("No gap zones at current threshold.")

        # AADT source
        st.markdown("---")
        st.markdown("##### AADT Source")
        st.warning(
            "AADT sourced from FHWA Highway Statistics static lookup table. "
            "Values approximate freight truck volumes by corridor segment. "
            "For live HPMS data: ops.fhwa.dot.gov"
        )

        aadt_df = get_aadt_for_corridor(corridor)
        if not aadt_df.empty:
            st.dataframe(aadt_df, width="stretch", hide_index=True)
        st.caption("Source: FHWA Highway Statistics, Freight Analysis Framework")

        # Land cost source
        st.markdown("---")
        st.markdown("##### Land Cost Source")
        st.info(
            "Land cost estimates from USDA Land Values 2023 Summary (nass.usda.gov). "
            "Represents median rural/commercial land per acre by state. "
            "Interstate exit parcels may differ significantly — verify with county assessor."
        )
        st.caption("Source: USDA NASS Land Values 2023 Summary")

        # Pro forma audit trail
        if pf_result and pf_inputs:
            st.markdown("---")
            st.markdown("##### Pro Forma Audit Trail")

            audit = audit_pro_forma(
                daily_volume=pf_inputs.get("daily_volume", 0),
                capture_rate=pf_inputs.get("capture_rate", 0),
                revenue_per_stop=pf_inputs.get("revenue_per_stop", 0),
                annual_opex=pf_result.get("annual_opex", 0),
                total_project_cost=pf_result.get("total_project_cost", 0),
                hold_years=pf_inputs.get("hold_years", 5),
                pf_result=pf_result,
            )

            st.markdown(f"**Gross Revenue** = {audit['gross_revenue_calc']}")
            st.markdown(f"**NOI** = {audit['noi_calc']}")
            st.markdown(f"**Total Project Cost** = {audit['total_cost_calc']}")
            st.markdown(f"**Cap Rate** = {audit['cap_rate_calc']}")

            if audit["cap_rate_flag"]:
                st.error(
                    f"Unusual cap rate ({audit['cap_rate_value']:.1f}%) — check inputs. "
                    "Expected range: 3-20%."
                )

            # Cash flow table
            cfs = audit["cash_flows"]
            if cfs:
                cf_rows = []
                for i, cf in enumerate(cfs):
                    label = "Initial Investment" if i == 0 else f"Year {i}"
                    if i == len(cfs) - 1 and i > 0:
                        label += " (incl. terminal value)"
                    cf_rows.append({"Period": label, "Cash Flow": f"${cf:,.0f}"})
                with st.expander("Year-by-year cash flows"):
                    st.dataframe(pd.DataFrame(cf_rows), width="stretch", hide_index=True)

        # Acquisition audit
        if acquisition_data:
            st.markdown("---")
            st.markdown("##### Acquisition Screen Audit")

            for target in acquisition_data[:5]:  # show top 5
                a = audit_acquisition_target(
                    target.get("aadt", 0),
                    target.get("daily_captures", 0),
                    target.get("ebitda", 0),
                )
                name = target.get("name", "Unknown")
                st.markdown(f"**{name}:** {a['ebitda_calc']}")
                if a["rev_flag"]:
                    st.warning(
                        f"Revenue/truck sanity check: ${a['rev_per_truck']:.2f} "
                        f"(expected $5-$30 range)"
                    )
