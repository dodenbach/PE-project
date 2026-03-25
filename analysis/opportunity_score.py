"""Composite opportunity scoring for gap zones."""

import numpy as np


def score_gap_zone(gap_miles: float, aadt: int, land_cost_per_acre: float) -> dict:
    """
    Weighted composite score (0-100) for a gap zone.

    Components:
    - Gap severity: 40% (higher gap = more captive demand)
    - AADT: 35% (more trucks = more revenue potential)
    - Land cost inverse: 25% (cheaper land = better margins)

    Returns dict with total_score and component breakdown.
    """
    # Normalize gap severity (80-300 mile range)
    gap_norm = np.clip((gap_miles - 80) / (300 - 80), 0, 1)

    # Normalize AADT (2000-15000 trucks/day range)
    aadt_norm = np.clip((aadt - 2000) / (15000 - 2000), 0, 1)

    # Normalize land cost inverse (cheaper = higher score)
    # Range: $1000/acre (cheapest) to $200,000/acre (most expensive)
    land_norm = np.clip(1 - (land_cost_per_acre - 1000) / (200000 - 1000), 0, 1)

    # Weighted composite
    gap_weight = 0.40
    aadt_weight = 0.35
    land_weight = 0.25

    gap_score = gap_norm * 100
    aadt_score = aadt_norm * 100
    land_score = land_norm * 100

    total = (gap_score * gap_weight + aadt_score * aadt_weight + land_score * land_weight)

    return {
        "total_score": round(total, 1),
        "gap_score": round(gap_score, 1),
        "gap_weight": gap_weight,
        "aadt_score": round(aadt_score, 1),
        "aadt_weight": aadt_weight,
        "land_score": round(land_score, 1),
        "land_weight": land_weight,
        "gap_miles": gap_miles,
        "aadt": aadt,
        "land_cost_per_acre": land_cost_per_acre,
    }


def score_label(score: float) -> str:
    """Return a human-readable label for a score."""
    if score >= 75:
        return "Strong Opportunity"
    elif score >= 55:
        return "Moderate Opportunity"
    elif score >= 35:
        return "Marginal"
    return "Weak"


def score_color(score: float) -> str:
    """Return a hex color for a score."""
    if score >= 75:
        return "#22C55E"  # green
    elif score >= 55:
        return "#F59E0B"  # amber
    elif score >= 35:
        return "#F97316"  # orange
    return "#EF4444"  # red
