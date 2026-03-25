"""Fetch existing truck stops — static data with Overpass API fallback."""

import json
import os
import pandas as pd

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

MAJOR_OPERATORS = {"Pilot", "Love's", "Flying J", "TA", "Petro", "TravelCenters of America",
                   "Pilot Flying J", "Loves", "Love's Travel Stops"}

# Load pre-fetched stop data
_STATIC_STOPS = {}
_static_path = os.path.join(os.path.dirname(__file__), "static_stops.json")
if os.path.exists(_static_path):
    with open(_static_path) as f:
        _STATIC_STOPS = json.load(f)


def fetch_stops(corridor: str) -> pd.DataFrame:
    """Return truck stops as DataFrame. Uses pre-fetched static data, falls back to Overpass."""

    if corridor in _STATIC_STOPS:
        df = pd.DataFrame(_STATIC_STOPS[corridor])
        if not df.empty:
            return df

    return _fetch_stops_live(corridor)


def _fetch_stops_live(corridor: str) -> pd.DataFrame:
    """Query Overpass for truck stops along a corridor."""
    import requests
    from data.fetch_routes import CORRIDOR_BBOXES

    bbox = CORRIDOR_BBOXES.get(corridor)
    if bbox is None:
        raise ValueError(f"Unknown corridor: {corridor}")

    s, w, n, e = bbox
    pad = 0.3
    s, w, n, e = s - pad, w - pad, n + pad, e + pad

    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="fuel"]["hgv"="yes"]({s},{w},{n},{e});
      node["amenity"="truck_stop"]({s},{w},{n},{e});
      way["amenity"="fuel"]["hgv"="yes"]({s},{w},{n},{e});
    );
    out center;
    """

    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue

        name = tags.get("name", "Unknown")
        operator = tags.get("operator", tags.get("brand", "Independent"))
        is_major = any(m.lower() in operator.lower() or m.lower() in name.lower()
                       for m in MAJOR_OPERATORS)

        rows.append({
            "name": name,
            "operator": operator,
            "lat": lat,
            "lon": lon,
            "is_major": is_major,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["name", "operator", "lat", "lon", "is_major"])
    return df.drop_duplicates(subset=["lat", "lon"]).reset_index(drop=True)
