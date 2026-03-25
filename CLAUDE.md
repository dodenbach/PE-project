# Truck Stop Site Screener

A three-panel deal screening tool for identifying truck stop development opportunities.

## What this does
1. Takes an interstate corridor as input (e.g., "I-80")
2. Pulls existing truck stop locations from OpenStreetMap
3. Runs HOS gap analysis to find under-served segments
4. Scores gap zones by traffic volume and land cost
5. Outputs a real estate pro forma (NOI, cap rate, IRR) for any selected zone

## Architecture
- `app.py` is the Streamlit entrypoint — all UI logic lives here
- `data/` contains all external API calls — keep these pure functions that return DataFrames
- `analysis/` contains all business logic — no API calls, no Streamlit imports
- `components/` contains Streamlit rendering functions — import from analysis/, not data/

## Code rules
- All data fetch functions must accept a corridor string and return a pandas DataFrame
- All analysis functions must be pure (no side effects, no API calls)
- Map rendering uses Folium — return folium.Map objects, render with st.components.html()
- Never hardcode coordinates — always derive from the corridor input
- Pro forma inputs should have sensible defaults that represent a realistic "bare lot" build

## Key constants (HOS regulations)
- Max driving time: 11 hours/day
- Required 30-min break: after 8 hours
- Average truck speed: 55 mph
- Therefore: trucks need a stop option every ~440 miles (8hrs x 55mph) at minimum
- Gap threshold for "opportunity": >80 miles between existing stops on a high-traffic corridor

## Data sources
- Routes + stops: Overpass API (https://overpass-api.de/api/interpreter) — no key needed
- Traffic: FHWA HPMS data, download CSV or use static table in data/fetch_aadt.py
- Land cost: Static table in data/land_costs.py keyed by state + rural/suburban/urban classification

## Style
- Streamlit theme: dark background, monospace accents, minimal chrome
- Map: dark tile layer (CartoDB dark_matter)
- Opportunity zones: highlighted in amber (#F59E0B)
- Gap severity: color-coded green -> yellow -> red

## Run
```bash
cd /Users/drewodenbach/Desktop/truck-stop-screener
source venv/bin/activate
streamlit run app.py
```
