"""Static AADT (Annual Average Daily Traffic) lookup by corridor and segment.

Source: FHWA Freight Analysis Framework, approximate truck volumes.
These are defensible order-of-magnitude figures for a screening tool.
"""

import pandas as pd

# Approximate AADT (trucks/day) by corridor segment
# Keyed by corridor -> list of (start_lon, end_lon, segment_name, truck_aadt)
CORRIDOR_AADT = {
    "I-80": [
        (-117.0, -112.0, "Reno to Salt Lake City", 4800),
        (-112.0, -108.0, "Salt Lake City to Rock Springs", 5200),
        (-108.0, -104.5, "Rock Springs to Cheyenne", 5800),
        (-104.5, -100.0, "Cheyenne to North Platte", 7200),
        (-100.0, -96.0, "North Platte to Lincoln", 8500),
        (-96.0, -92.0, "Lincoln to Des Moines", 9500),
        (-92.0, -88.0, "Des Moines to Iowa City", 10500),
        (-88.0, -84.0, "Iowa City to Joliet", 12000),
        (-84.0, -80.0, "Joliet to Toledo", 11500),
        (-80.0, -76.0, "Toledo to Youngstown", 10000),
        (-76.0, -74.0, "Youngstown to NJ", 13000),
    ],
    "I-40": [
        (-117.5, -112.0, "Barstow to Kingman", 5500),
        (-112.0, -108.0, "Kingman to Flagstaff", 6200),
        (-108.0, -104.0, "Flagstaff to Albuquerque", 7800),
        (-104.0, -100.0, "Albuquerque to Tucumcari", 5800),
        (-100.0, -96.0, "Tucumcari to Amarillo", 6500),
        (-96.0, -92.0, "Amarillo to OKC", 8200),
        (-92.0, -88.0, "OKC to Little Rock", 9500),
        (-88.0, -84.0, "Little Rock to Memphis", 11000),
        (-84.0, -80.0, "Memphis to Nashville", 12500),
        (-80.0, -78.0, "Nashville to Knoxville", 10000),
    ],
    "I-10": [
        (-118.5, -114.0, "LA to Palm Springs", 8500),
        (-114.0, -110.0, "Yuma to Tucson", 6200),
        (-110.0, -106.0, "Tucson to Las Cruces", 5500),
        (-106.0, -100.0, "Las Cruces to Fort Stockton", 4200),
        (-100.0, -96.0, "Fort Stockton to San Antonio", 7500),
        (-96.0, -92.0, "San Antonio to Houston", 12000),
        (-92.0, -88.0, "Houston to Lake Charles", 9800),
        (-88.0, -84.0, "Lake Charles to Baton Rouge", 10500),
        (-84.0, -81.0, "Mobile to Tallahassee", 7200),
    ],
    "I-70": [
        (-109.0, -106.0, "Grand Junction to Glenwood", 3200),
        (-106.0, -104.0, "Glenwood to Denver", 5800),
        (-104.0, -100.0, "Denver to Hays", 6500),
        (-100.0, -96.0, "Hays to Topeka", 7200),
        (-96.0, -92.0, "Topeka to KC", 11000),
        (-92.0, -88.0, "KC to Columbia", 9800),
        (-88.0, -84.0, "Columbia to St. Louis to Effingham", 12500),
        (-84.0, -80.0, "Indianapolis to Dayton", 13000),
        (-80.0, -76.5, "Columbus to Wheeling", 9500),
    ],
    "I-90": [
        (-122.5, -118.0, "Seattle to Ellensburg", 5500),
        (-118.0, -114.0, "Ellensburg to Spokane", 4800),
        (-114.0, -110.0, "Spokane to Missoula", 3500),
        (-110.0, -106.0, "Missoula to Billings", 3800),
        (-106.0, -100.0, "Billings to Rapid City", 4200),
        (-100.0, -96.0, "Rapid City to Sioux Falls", 5500),
        (-96.0, -92.0, "Sioux Falls to Albert Lea", 7000),
        (-92.0, -88.0, "Albert Lea to Madison", 8500),
        (-88.0, -84.0, "Madison to Chicago", 11500),
        (-84.0, -78.0, "Chicago to Cleveland", 10500),
        (-78.0, -74.0, "Cleveland to Buffalo", 8200),
        (-74.0, -71.0, "Buffalo to Albany to Boston", 7500),
    ],
}


def get_aadt_for_corridor(corridor: str) -> pd.DataFrame:
    """Return AADT data for a corridor as a DataFrame."""
    segments = CORRIDOR_AADT.get(corridor, [])
    if not segments:
        return pd.DataFrame(columns=["start_lon", "end_lon", "segment_name", "truck_aadt"])
    return pd.DataFrame(segments, columns=["start_lon", "end_lon", "segment_name", "truck_aadt"])


def get_aadt_at_lon(corridor: str, lon: float) -> int:
    """Return estimated truck AADT at a given longitude along a corridor."""
    segments = CORRIDOR_AADT.get(corridor, [])
    for start_lon, end_lon, _, aadt in segments:
        if start_lon <= lon <= end_lon:
            return aadt
    # Return nearest segment's AADT if out of range
    if segments:
        dists = [(abs(lon - (s[0] + s[1]) / 2), s[3]) for s in segments]
        dists.sort()
        return dists[0][1]
    return 5000  # fallback
