"""Panel 1: Corridor map with route, stops, and gap zones."""

import folium
import pandas as pd
from folium.plugins import MarkerCluster

SEVERITY_COLORS = {
    "low": "#22C55E",
    "medium": "#F59E0B",
    "high": "#EF4444",
}


def build_corridor_map(
    route_df: pd.DataFrame,
    stops_df: pd.DataFrame,
    gaps_df: pd.DataFrame,
    center: tuple = (39.0, -98.0),
    zoom: int = 5,
) -> folium.Map:
    """Build Folium map showing corridor, stops, and gap zones."""

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Draw route line
    if not route_df.empty:
        # Sample route points to keep map performant (max 2000 points)
        if len(route_df) > 2000:
            step = len(route_df) // 2000
            sampled = route_df.iloc[::step]
        else:
            sampled = route_df

        coords = list(zip(sampled["lat"], sampled["lon"]))
        if coords:
            folium.PolyLine(
                coords,
                color="#FFFFFF",
                weight=3,
                opacity=0.7,
            ).add_to(m)

    # Draw gap zones
    if not gaps_df.empty:
        for _, gap in gaps_df.iterrows():
            color = SEVERITY_COLORS.get(gap["severity"], "#F59E0B")

            # Draw gap zone as a highlighted polyline segment
            folium.PolyLine(
                [
                    (gap["start_lat"], gap["start_lon"]),
                    (gap["mid_lat"], gap["mid_lon"]),
                    (gap["end_lat"], gap["end_lon"]),
                ],
                color=color,
                weight=8,
                opacity=0.8,
            ).add_to(m)

            # Add gap zone marker at midpoint
            folium.CircleMarker(
                location=(gap["mid_lat"], gap["mid_lon"]),
                radius=12,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=folium.Popup(
                    f"<div style='font-family: monospace; color: #fff; background: #1a1a1a; "
                    f"padding: 8px; border-radius: 4px; min-width: 200px;'>"
                    f"<b style='color: {color};'>{gap['severity'].upper()} GAP</b><br>"
                    f"<b>{gap['gap_miles']} miles</b><br>"
                    f"Between: {gap.get('nearest_stop_before', 'N/A')}<br>"
                    f"And: {gap.get('nearest_stop_after', 'N/A')}"
                    f"</div>",
                    max_width=300,
                ),
                tooltip=f"{gap['gap_miles']}mi gap ({gap['severity']})",
            ).add_to(m)

    # Draw truck stops
    if not stops_df.empty:
        cluster = MarkerCluster(name="Truck Stops").add_to(m)
        for _, stop in stops_df.iterrows():
            color = "#3B82F6" if stop.get("is_major") else "#6B7280"
            icon = "star" if stop.get("is_major") else "map-marker"

            folium.Marker(
                location=(stop["lat"], stop["lon"]),
                popup=folium.Popup(
                    f"<div style='font-family: monospace; color: #fff; background: #1a1a1a; "
                    f"padding: 8px; border-radius: 4px;'>"
                    f"<b>{stop['name']}</b><br>"
                    f"Operator: {stop['operator']}<br>"
                    f"{'Major Chain' if stop.get('is_major') else 'Independent'}"
                    f"</div>",
                    max_width=250,
                ),
                tooltip=stop["name"],
                icon=folium.Icon(color="blue" if stop.get("is_major") else "gray",
                                  icon=icon, prefix="fa"),
            ).add_to(cluster)

    # Add legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(10,10,10,0.9); padding: 12px 16px;
                border-radius: 8px; border: 1px solid #333;
                font-family: 'Courier New', monospace; font-size: 12px; color: #fff;">
        <div style="margin-bottom: 6px;"><b>Gap Severity</b></div>
        <div><span style="color: #22C55E;">&#9632;</span> Low (80-120 mi)</div>
        <div><span style="color: #F59E0B;">&#9632;</span> Medium (120-180 mi)</div>
        <div><span style="color: #EF4444;">&#9632;</span> High (180+ mi)</div>
        <div style="margin-top: 8px;"><b>Stops</b></div>
        <div><span style="color: #3B82F6;">&#9733;</span> Major Chain</div>
        <div><span style="color: #6B7280;">&#9679;</span> Independent</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m
