"""Fetch interstate highway geometry — static data with Overpass API fallback."""

import json
import os
import pandas as pd

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Corridor name -> (south, west, north, east) bounding box
CORRIDOR_BBOXES = {
    "I-80": (40.0, -117.0, 42.5, -74.0),
    "I-40": (34.5, -117.5, 36.5, -78.0),
    "I-10": (29.0, -118.5, 32.0, -81.0),
    "I-70": (38.0, -109.0, 40.5, -76.5),
    "I-90": (41.0, -122.5, 48.0, -71.0),
}

# Load pre-fetched route geometry
_STATIC_ROUTES = {}
_static_path = os.path.join(os.path.dirname(__file__), "static_routes.json")
if os.path.exists(_static_path):
    with open(_static_path) as f:
        _STATIC_ROUTES = json.load(f)


def fetch_route(corridor: str) -> pd.DataFrame:
    """Return route geometry as DataFrame with lat, lon, sequence columns.
    Uses pre-fetched static data. Falls back to Overpass API if not available."""

    # Use static data first
    if corridor in _STATIC_ROUTES:
        df = pd.DataFrame(_STATIC_ROUTES[corridor])
        if not df.empty:
            return df

    # Fallback: live Overpass query
    return _fetch_route_live(corridor)


def _fetch_route_live(corridor: str) -> pd.DataFrame:
    """Query Overpass for interstate geometry."""
    import requests

    bbox = CORRIDOR_BBOXES.get(corridor)
    if bbox is None:
        raise ValueError(f"Unknown corridor: {corridor}")

    s, w, n, e = bbox
    ref = corridor.replace("I-", "I ")

    query = f"""
    [out:json][timeout:60];
    (
      way["ref"~"{ref}"]["highway"~"motorway"]({s},{w},{n},{e});
    );
    out geom;
    """

    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    seq = 0
    for element in data.get("elements", []):
        if "geometry" in element:
            for pt in element["geometry"]:
                rows.append({
                    "lat": pt["lat"],
                    "lon": pt["lon"],
                    "sequence": seq,
                })
                seq += 1

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["lat", "lon", "sequence"])

    df = df.drop_duplicates(subset=["lat", "lon"]).reset_index(drop=True)
    df = df.sort_values("lon").reset_index(drop=True)
    df["sequence"] = range(len(df))
    return df


def get_corridor_center(corridor: str) -> tuple:
    """Return (lat, lon) center of a corridor's bounding box."""
    bbox = CORRIDOR_BBOXES.get(corridor)
    if bbox is None:
        return (39.0, -98.0)
    s, w, n, e = bbox
    return ((s + n) / 2, (w + e) / 2)


def get_corridor_bbox(corridor: str) -> tuple:
    """Return (south, west, north, east) bounding box."""
    return CORRIDOR_BBOXES.get(corridor, (29.0, -122.5, 48.0, -71.0))
