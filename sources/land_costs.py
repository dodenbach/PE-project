"""Static land cost lookup by state and classification.

Source: USDA National Agricultural Statistics Service, Land Values reports (2024).
Values represent median $/acre for agricultural/commercial land.
Urban/suburban values adjusted upward based on CoStar market data.
"""

# (state_abbr, classification) -> median $/acre
LAND_COSTS = {
    # Western states
    ("CA", "urban"): 250000,
    ("CA", "suburban"): 120000,
    ("CA", "rural"): 12500,
    ("NV", "urban"): 85000,
    ("NV", "suburban"): 35000,
    ("NV", "rural"): 1800,
    ("AZ", "urban"): 95000,
    ("AZ", "suburban"): 40000,
    ("AZ", "rural"): 2200,
    ("UT", "urban"): 80000,
    ("UT", "suburban"): 32000,
    ("UT", "rural"): 2000,
    ("NM", "urban"): 45000,
    ("NM", "suburban"): 18000,
    ("NM", "rural"): 1500,
    ("CO", "urban"): 110000,
    ("CO", "suburban"): 45000,
    ("CO", "rural"): 3200,

    # Mountain / Plains states
    ("WY", "urban"): 35000,
    ("WY", "suburban"): 15000,
    ("WY", "rural"): 1200,
    ("MT", "urban"): 40000,
    ("MT", "suburban"): 18000,
    ("MT", "rural"): 1400,
    ("ID", "urban"): 55000,
    ("ID", "suburban"): 22000,
    ("ID", "rural"): 3500,
    ("SD", "urban"): 30000,
    ("SD", "suburban"): 12000,
    ("SD", "rural"): 2800,
    ("ND", "urban"): 28000,
    ("ND", "suburban"): 10000,
    ("ND", "rural"): 2500,
    ("NE", "urban"): 40000,
    ("NE", "suburban"): 16000,
    ("NE", "rural"): 3800,
    ("KS", "urban"): 38000,
    ("KS", "suburban"): 15000,
    ("KS", "rural"): 3200,

    # Midwest
    ("IA", "urban"): 55000,
    ("IA", "suburban"): 25000,
    ("IA", "rural"): 9500,
    ("MN", "urban"): 65000,
    ("MN", "suburban"): 28000,
    ("MN", "rural"): 6500,
    ("WI", "urban"): 60000,
    ("WI", "suburban"): 25000,
    ("WI", "rural"): 5800,
    ("IL", "urban"): 120000,
    ("IL", "suburban"): 45000,
    ("IL", "rural"): 8500,
    ("IN", "urban"): 55000,
    ("IN", "suburban"): 22000,
    ("IN", "rural"): 7200,
    ("MO", "urban"): 48000,
    ("MO", "suburban"): 18000,
    ("MO", "rural"): 4500,
    ("OH", "urban"): 65000,
    ("OH", "suburban"): 25000,
    ("OH", "rural"): 7000,
    ("MI", "urban"): 55000,
    ("MI", "suburban"): 20000,
    ("MI", "rural"): 5500,

    # Southern states
    ("TX", "urban"): 95000,
    ("TX", "suburban"): 38000,
    ("TX", "rural"): 3500,
    ("OK", "urban"): 35000,
    ("OK", "suburban"): 14000,
    ("OK", "rural"): 2800,
    ("AR", "urban"): 30000,
    ("AR", "suburban"): 12000,
    ("AR", "rural"): 3200,
    ("LA", "urban"): 42000,
    ("LA", "suburban"): 18000,
    ("LA", "rural"): 3800,
    ("MS", "urban"): 28000,
    ("MS", "suburban"): 12000,
    ("MS", "rural"): 2800,
    ("AL", "urban"): 35000,
    ("AL", "suburban"): 14000,
    ("AL", "rural"): 3200,
    ("TN", "urban"): 55000,
    ("TN", "suburban"): 22000,
    ("TN", "rural"): 4500,
    ("FL", "urban"): 120000,
    ("FL", "suburban"): 48000,
    ("FL", "rural"): 8500,
    ("GA", "urban"): 65000,
    ("GA", "suburban"): 25000,
    ("GA", "rural"): 4200,
    ("NC", "urban"): 60000,
    ("NC", "suburban"): 22000,
    ("NC", "rural"): 5000,

    # Northeast / Mid-Atlantic
    ("PA", "urban"): 85000,
    ("PA", "suburban"): 35000,
    ("PA", "rural"): 7500,
    ("NY", "urban"): 150000,
    ("NY", "suburban"): 55000,
    ("NY", "rural"): 5200,
    ("NJ", "urban"): 180000,
    ("NJ", "suburban"): 85000,
    ("NJ", "rural"): 15000,
    ("WV", "urban"): 25000,
    ("WV", "suburban"): 10000,
    ("WV", "rural"): 2200,
    ("MD", "urban"): 120000,
    ("MD", "suburban"): 50000,
    ("MD", "rural"): 9500,
    ("MA", "urban"): 200000,
    ("MA", "suburban"): 80000,
    ("MA", "rural"): 12000,
    ("CT", "urban"): 180000,
    ("CT", "suburban"): 70000,
    ("CT", "rural"): 11000,

    # Pacific Northwest
    ("WA", "urban"): 130000,
    ("WA", "suburban"): 50000,
    ("WA", "rural"): 4500,
    ("OR", "urban"): 95000,
    ("OR", "suburban"): 38000,
    ("OR", "rural"): 3800,
}

# Longitude -> approximate state mapping for corridor analysis
LON_TO_STATE = {
    "I-80": [
        (-117.0, -114.5, "NV"), (-114.5, -112.0, "UT"), (-112.0, -111.0, "UT"),
        (-111.0, -104.0, "WY"), (-104.0, -97.0, "NE"), (-97.0, -91.0, "IA"),
        (-91.0, -87.5, "IL"), (-87.5, -84.5, "IN"), (-84.5, -80.5, "OH"),
        (-80.5, -76.0, "PA"), (-76.0, -74.0, "NJ"),
    ],
    "I-40": [
        (-117.5, -114.5, "CA"), (-114.5, -109.0, "AZ"), (-109.0, -103.0, "NM"),
        (-103.0, -100.0, "TX"), (-100.0, -94.5, "OK"), (-94.5, -90.0, "AR"),
        (-90.0, -88.0, "TN"), (-88.0, -84.0, "TN"), (-84.0, -78.0, "NC"),
    ],
    "I-10": [
        (-118.5, -114.5, "CA"), (-114.5, -109.0, "AZ"), (-109.0, -104.0, "NM"),
        (-104.0, -94.0, "TX"), (-94.0, -89.0, "LA"), (-89.0, -85.0, "MS"),
        (-85.0, -81.0, "FL"),
    ],
    "I-70": [
        (-109.0, -102.0, "CO"), (-102.0, -97.0, "KS"), (-97.0, -91.5, "MO"),
        (-91.5, -87.5, "IL"), (-87.5, -84.5, "IN"), (-84.5, -80.5, "OH"),
        (-80.5, -76.5, "WV"),
    ],
    "I-90": [
        (-122.5, -117.0, "WA"), (-117.0, -116.0, "ID"), (-116.0, -104.0, "MT"),
        (-104.0, -96.5, "SD"), (-96.5, -91.0, "MN"), (-91.0, -87.5, "WI"),
        (-87.5, -84.5, "IN"), (-84.5, -80.5, "OH"), (-80.5, -76.0, "PA"),
        (-76.0, -74.0, "NY"), (-74.0, -71.0, "MA"),
    ],
}


def get_state_at_lon(corridor: str, lon: float) -> str:
    """Return state abbreviation for a given longitude along a corridor."""
    segments = LON_TO_STATE.get(corridor, [])
    for start, end, state in segments:
        if start <= lon <= end:
            return state
    return "TX"  # fallback


def get_land_cost(state: str, classification: str = "rural") -> float:
    """Return land cost $/acre for a given state and classification."""
    cost = LAND_COSTS.get((state, classification))
    if cost is not None:
        return cost
    # Fallback: try rural
    cost = LAND_COSTS.get((state, "rural"))
    if cost is not None:
        return cost
    return 5000  # national rural average fallback


def classify_location(lon: float, corridor: str) -> str:
    """Simple classification based on known urban centers along corridors.
    Returns 'urban', 'suburban', or 'rural'."""
    # Major metro longitudes (approximate city centers)
    urban_lons = {
        "I-80": [-87.6, -83.5, -93.6, -95.9, -111.9, -74.2],  # Chicago, Toledo, Des Moines, Omaha, SLC, NJ
        "I-40": [-117.3, -111.6, -106.6, -97.5, -92.3, -90.0, -86.8],  # Barstow, Flagstaff, ABQ, OKC, LR, Memphis, Nashville
        "I-10": [-118.2, -111.9, -106.4, -98.5, -95.4, -93.2, -90.1],  # LA, Tucson, El Paso, SA, Houston, LC, BR
        "I-70": [-104.9, -94.6, -90.2, -86.2, -83.0, -80.2],  # Denver, KC, STL, Indy, Columbus, WV
        "I-90": [-122.3, -117.4, -113.9, -96.7, -89.4, -87.6, -81.7],  # Seattle, Spokane, Missoula, SF, Madison, Chicago, Cleveland
    }
    suburban_radius = 0.5  # degrees longitude
    urban_radius = 0.15

    metros = urban_lons.get(corridor, [])
    for metro_lon in metros:
        dist = abs(lon - metro_lon)
        if dist < urban_radius:
            return "urban"
        if dist < suburban_radius:
            return "suburban"
    return "rural"
