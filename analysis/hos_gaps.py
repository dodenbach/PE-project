"""HOS gap analysis — identify under-served segments along a corridor."""

import numpy as np
import pandas as pd

# Earth radius in miles
EARTH_RADIUS_MI = 3958.8


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two points."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MI * np.arcsin(np.sqrt(a))


def project_stops_onto_route(route_df: pd.DataFrame, stops_df: pd.DataFrame,
                              max_dist_miles: float = 25.0) -> pd.DataFrame:
    """Project each stop onto the nearest route point. Returns stops with route_sequence and distance."""
    if route_df.empty or stops_df.empty:
        return stops_df.assign(route_sequence=[], dist_to_route=[])

    projected = []
    for _, stop in stops_df.iterrows():
        dists = haversine(stop["lat"], stop["lon"],
                          route_df["lat"].values, route_df["lon"].values)
        min_idx = np.argmin(dists)
        min_dist = dists[min_idx]

        if min_dist <= max_dist_miles:
            projected.append({
                **stop.to_dict(),
                "route_sequence": route_df.iloc[min_idx]["sequence"],
                "dist_to_route": min_dist,
            })

    if not projected:
        return pd.DataFrame(columns=list(stops_df.columns) + ["route_sequence", "dist_to_route"])
    return pd.DataFrame(projected).sort_values("route_sequence").reset_index(drop=True)


def cumulative_route_distance(route_df: pd.DataFrame) -> np.ndarray:
    """Calculate cumulative distance along route in miles."""
    if len(route_df) < 2:
        return np.array([0.0])

    lats = route_df["lat"].values
    lons = route_df["lon"].values
    segment_dists = haversine(lats[:-1], lons[:-1], lats[1:], lons[1:])
    return np.concatenate([[0.0], np.cumsum(segment_dists)])


def find_gap_zones(route_df: pd.DataFrame, stops_df: pd.DataFrame,
                   gap_threshold_miles: float = 80.0) -> pd.DataFrame:
    """
    Walk the route and find segments where the gap between stops exceeds threshold.

    Returns DataFrame with columns:
        start_lat, start_lon, end_lat, end_lon, mid_lat, mid_lon,
        gap_miles, severity, nearest_stops
    """
    if route_df.empty:
        return pd.DataFrame(columns=["start_lat", "start_lon", "end_lat", "end_lon",
                                      "mid_lat", "mid_lon", "gap_miles", "severity",
                                      "nearest_stop_before", "nearest_stop_after"])

    # Project stops onto route
    projected = project_stops_onto_route(route_df, stops_df)
    if projected.empty:
        # Entire route is a gap
        return pd.DataFrame([{
            "start_lat": route_df.iloc[0]["lat"],
            "start_lon": route_df.iloc[0]["lon"],
            "end_lat": route_df.iloc[-1]["lat"],
            "end_lon": route_df.iloc[-1]["lon"],
            "mid_lat": route_df["lat"].mean(),
            "mid_lon": route_df["lon"].mean(),
            "gap_miles": 999,
            "severity": "high",
            "nearest_stop_before": "None",
            "nearest_stop_after": "None",
        }])

    # Calculate cumulative distances along route
    cum_dist = cumulative_route_distance(route_df)

    # Get stop positions along route by distance
    stop_positions = []
    for _, stop in projected.iterrows():
        seq = int(stop["route_sequence"])
        seq = min(seq, len(cum_dist) - 1)
        stop_positions.append({
            "name": stop["name"],
            "distance": cum_dist[seq],
            "lat": stop["lat"],
            "lon": stop["lon"],
            "sequence": seq,
        })

    stop_positions.sort(key=lambda x: x["distance"])

    # Find gaps between consecutive stops
    gaps = []
    for i in range(len(stop_positions) - 1):
        s1 = stop_positions[i]
        s2 = stop_positions[i + 1]
        gap_miles = s2["distance"] - s1["distance"]

        if gap_miles >= gap_threshold_miles:
            # Find midpoint on route
            mid_seq = (s1["sequence"] + s2["sequence"]) // 2
            mid_seq = min(mid_seq, len(route_df) - 1)
            mid_pt = route_df.iloc[mid_seq]

            # Start and end of gap zone (1/4 and 3/4 points for the highlighted zone)
            q1_seq = s1["sequence"] + (s2["sequence"] - s1["sequence"]) // 4
            q3_seq = s1["sequence"] + 3 * (s2["sequence"] - s1["sequence"]) // 4
            q1_seq = min(q1_seq, len(route_df) - 1)
            q3_seq = min(q3_seq, len(route_df) - 1)

            severity = _classify_severity(gap_miles)

            gaps.append({
                "start_lat": route_df.iloc[q1_seq]["lat"],
                "start_lon": route_df.iloc[q1_seq]["lon"],
                "end_lat": route_df.iloc[q3_seq]["lat"],
                "end_lon": route_df.iloc[q3_seq]["lon"],
                "mid_lat": mid_pt["lat"],
                "mid_lon": mid_pt["lon"],
                "gap_miles": round(gap_miles, 1),
                "severity": severity,
                "nearest_stop_before": s1["name"],
                "nearest_stop_after": s2["name"],
            })

    if not gaps:
        return pd.DataFrame(columns=["start_lat", "start_lon", "end_lat", "end_lon",
                                      "mid_lat", "mid_lon", "gap_miles", "severity",
                                      "nearest_stop_before", "nearest_stop_after"])
    return pd.DataFrame(gaps).sort_values("gap_miles", ascending=False).reset_index(drop=True)


def _classify_severity(gap_miles: float) -> str:
    """Classify gap severity."""
    if gap_miles >= 180:
        return "high"
    elif gap_miles >= 120:
        return "medium"
    return "low"
