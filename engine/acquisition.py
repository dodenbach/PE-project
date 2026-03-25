"""Acquisition screener — score independent truck stops as buyout targets."""

import numpy as np
import pandas as pd

from engine.hos_gaps import haversine

MAJOR_OPERATORS = {
    "pilot", "love's", "loves", "flying j", "pilot flying j",
    "ta", "petro", "travelcenters of america", "speedway", "marathon",
}

EBITDA_MARGIN = 0.28  # NATSO independent operator industry average
CAPTURE_RATE = 0.08   # Conservative independent capture rate
REVENUE_PER_STOP = 14  # Blended average: parking fee + fuel margin


def classify_stops(stops_df: pd.DataFrame) -> pd.DataFrame:
    """Reclassify stops as major/independent using expanded operator list."""
    if stops_df.empty:
        return stops_df

    df = stops_df.copy()

    def _is_major(row):
        name = str(row.get("name", "")).lower()
        op = str(row.get("operator", "")).lower()
        return any(m in op or m in name for m in MAJOR_OPERATORS)

    df["is_major"] = df.apply(_is_major, axis=1)
    return df


def get_independents(stops_df: pd.DataFrame) -> pd.DataFrame:
    """Filter to independent (non-major-chain) stops only."""
    df = classify_stops(stops_df)
    return df[~df["is_major"]].reset_index(drop=True)


def score_acquisition_target(
    stop_lat: float,
    stop_lon: float,
    gaps_df: pd.DataFrame,
    aadt: int,
    land_cost_per_acre: float,
    gap_proximity_miles: float = 20.0,
) -> dict:
    """
    Score an independent stop as an acquisition target (0-100).

    Components:
    - Gap proximity: 40 pts if within gap_proximity_miles of a gap zone
    - AADT: up to 35 pts (normalized 2000-15000)
    - Land cost inverse: up to 25 pts (cheaper = better margins)
    """
    # Gap proximity score
    gap_score = 0.0
    near_gap = False
    if not gaps_df.empty:
        for _, gap in gaps_df.iterrows():
            dist = haversine(stop_lat, stop_lon, gap["mid_lat"], gap["mid_lon"])
            if dist <= gap_proximity_miles:
                gap_score = 40.0
                near_gap = True
                break

    # AADT score (0-35)
    aadt_norm = np.clip((aadt - 2000) / (15000 - 2000), 0, 1)
    aadt_score = aadt_norm * 35.0

    # Land cost inverse score (0-25)
    land_norm = np.clip(1 - (land_cost_per_acre - 1000) / (200000 - 1000), 0, 1)
    land_score = land_norm * 25.0

    total = gap_score + aadt_score + land_score

    return {
        "location_score": round(total, 1),
        "gap_proximity_score": round(gap_score, 1),
        "near_gap": near_gap,
        "aadt_score": round(aadt_score, 1),
        "land_score": round(land_score, 1),
        "aadt": aadt,
        "land_cost_per_acre": land_cost_per_acre,
    }


def compute_unit_economics(aadt: int) -> dict:
    """Compute unit economics for an independent stop."""
    daily_captures = aadt * CAPTURE_RATE
    annual_gross_revenue = daily_captures * REVENUE_PER_STOP * 365
    ebitda = annual_gross_revenue * EBITDA_MARGIN

    return {
        "daily_captures": round(daily_captures, 1),
        "annual_gross_revenue": round(annual_gross_revenue),
        "ebitda": round(ebitda),
        "revenue_per_stop": REVENUE_PER_STOP,
        "capture_rate": CAPTURE_RATE,
        "ebitda_margin": EBITDA_MARGIN,
    }


def acquisition_price_table(ebitda: float) -> pd.DataFrame:
    """Return 3-row acquisition price table at different multiples."""
    rows = [
        {"Multiple": "4x EBITDA", "Label": "Distressed", "Implied Price": f"${ebitda * 4:,.0f}"},
        {"Multiple": "5x EBITDA", "Label": "Fair Value", "Implied Price": f"${ebitda * 5:,.0f}"},
        {"Multiple": "6x EBITDA", "Label": "Premium", "Implied Price": f"${ebitda * 6:,.0f}"},
    ]
    return pd.DataFrame(rows)


def count_rollup_targets(
    stop_lat: float,
    stop_lon: float,
    independents_df: pd.DataFrame,
    radius_miles: float = 300.0,
) -> int:
    """Count independent stops within radius on the same corridor."""
    if independents_df.empty:
        return 0
    dists = haversine(
        stop_lat, stop_lon,
        independents_df["lat"].values, independents_df["lon"].values,
    )
    return int(np.sum(dists <= radius_miles)) - 1  # exclude self
