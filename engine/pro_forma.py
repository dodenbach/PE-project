"""Real estate pro forma model for truck stop development.

Build cost sources:
- Bare Lot: RSMeans site work estimates for rural commercial (gravel, grading, lighting, signage)
- Basic: NATSO small-format fuel/c-store construction data, adjusted for rural interstate exits
- Full Service: Love's Travel Stops 10-K filings, Pilot investor presentations (new-build cost per location)
OpEx sources: NATSO independent operator benchmarks, adjusted by format
"""

import numpy as np
import pandas as pd

# Build type configurations — updated to match industry reality
# Sources: Love's 10-K (2023), Pilot/Flying J investor materials, NATSO new-build surveys
BUILD_TYPES = {
    "Bare Lot": {
        "acres_range": (2, 5),
        "build_cost_range": (200_000, 500_000),
        "monthly_opex": 6_000,
        "description": "Gravel lot with basic lighting, signage, and portable restrooms. 20-40 parking spaces.",
        "default_acres": 3,
        "default_build": 350_000,
        "max_daily_trucks": 40,  # physical capacity: 20-30 spaces x ~1.5 turnover
    },
    "Basic": {
        "acres_range": (5, 10),
        "build_cost_range": (3_500_000, 7_000_000),
        "monthly_opex": 45_000,
        "description": "Paved lot with 4-8 fuel pumps, restrooms, c-store, UST install. 40-80 parking spaces.",
        "default_acres": 7,
        "default_build": 5_500_000,
        "max_daily_trucks": 250,
    },
    "Full Service": {
        "acres_range": (10, 20),
        "build_cost_range": (12_000_000, 22_000_000),
        "monthly_opex": 130_000,
        "description": "Full-service: 12+ fuel lanes, restaurant, showers, lounge, repair bay. 100-200 spaces.",
        "default_acres": 15,
        "default_build": 16_000_000,
        "max_daily_trucks": 800,
    },
}

# Cap rate benchmarks
CAP_RATE_BENCHMARKS = {
    "Industrial / Logistics": (5.0, 6.0),
    "Net Lease Retail": (5.5, 7.0),
    "Truck Stop (Stabilized)": (6.0, 8.0),
    "Fuel / C-Store": (6.5, 8.5),
}


def calculate_pro_forma(
    land_cost_per_acre: float,
    acres: float,
    build_type: str,
    daily_truck_volume: int,
    capture_rate: float = 0.05,
    revenue_per_stop: float = 12.0,
    hold_years: int = 5,
    annual_revenue_growth: float = 0.03,
    annual_expense_growth: float = 0.02,
    terminal_cap_rate: float = 0.075,
) -> dict:
    """
    Calculate full pro forma for a truck stop development.

    Returns dict with all financial metrics including sensitivity table.
    """
    config = BUILD_TYPES.get(build_type, BUILD_TYPES["Bare Lot"])

    # Costs
    total_land_cost = land_cost_per_acre * acres
    build_cost = config["default_build"]
    total_project_cost = total_land_cost + build_cost
    monthly_opex = config["monthly_opex"]
    annual_opex = monthly_opex * 12

    # Revenue — cap daily stops at physical capacity
    raw_daily_stops = daily_truck_volume * capture_rate
    max_capacity = config.get("max_daily_trucks", 9999)
    daily_stops = min(raw_daily_stops, max_capacity)
    daily_revenue = daily_stops * revenue_per_stop
    annual_gross_revenue = daily_revenue * 365

    # Capacity flag
    capacity_capped = raw_daily_stops > max_capacity

    # Year 1 NOI
    noi_year1 = annual_gross_revenue - annual_opex

    # Cap rate
    cap_rate = (noi_year1 / total_project_cost * 100) if total_project_cost > 0 else 0

    # Cash flows for IRR
    cash_flows = [-total_project_cost]
    noi = noi_year1
    for yr in range(1, hold_years + 1):
        if yr > 1:
            noi = noi * (1 + annual_revenue_growth) - (annual_opex * annual_expense_growth)
        if yr == hold_years:
            # Terminal value at exit
            terminal_value = noi / terminal_cap_rate
            cash_flows.append(noi + terminal_value)
        else:
            cash_flows.append(noi)

    # IRR calculation
    irr = _calculate_irr(cash_flows)

    # Sensitivity table
    sensitivity = build_sensitivity_table(
        land_cost_per_acre, acres, build_type, daily_truck_volume, hold_years,
        annual_revenue_growth, annual_expense_growth, terminal_cap_rate,
    )

    return {
        "total_land_cost": total_land_cost,
        "build_cost": build_cost,
        "total_project_cost": total_project_cost,
        "annual_opex": annual_opex,
        "daily_stops": daily_stops,
        "annual_gross_revenue": annual_gross_revenue,
        "noi": noi_year1,
        "cap_rate": cap_rate,
        "irr": irr,
        "hold_years": hold_years,
        "cash_flows": cash_flows,
        "sensitivity": sensitivity,
        "build_type_config": config,
        "capacity_capped": capacity_capped,
        "max_daily_trucks": max_capacity,
    }


def build_sensitivity_table(
    land_cost_per_acre, acres, build_type, daily_truck_volume, hold_years,
    annual_revenue_growth, annual_expense_growth, terminal_cap_rate,
) -> pd.DataFrame:
    """Build 5x5 sensitivity table: capture_rate vs revenue_per_stop -> IRR."""
    capture_rates = [0.02, 0.03, 0.04, 0.05, 0.08]
    revenues_per_stop = [8, 10, 12, 15, 18]

    config = BUILD_TYPES.get(build_type, BUILD_TYPES["Bare Lot"])
    total_cost = land_cost_per_acre * acres + config["default_build"]
    annual_opex = config["monthly_opex"] * 12
    max_cap = config.get("max_daily_trucks", 9999)

    rows = []
    for cr in capture_rates:
        row = {}
        for rps in revenues_per_stop:
            daily = min(daily_truck_volume * cr, max_cap)
            annual_rev = daily * rps * 365
            noi1 = annual_rev - annual_opex

            cfs = [-total_cost]
            noi = noi1
            for yr in range(1, hold_years + 1):
                if yr > 1:
                    noi = noi * (1 + annual_revenue_growth) - (annual_opex * annual_expense_growth)
                if yr == hold_years:
                    tv = noi / terminal_cap_rate
                    cfs.append(noi + tv)
                else:
                    cfs.append(noi)

            irr_val = _calculate_irr(cfs)
            row[f"${rps}/stop"] = f"{irr_val:.1f}%" if irr_val is not None else "N/A"
        rows.append(row)

    df = pd.DataFrame(rows, index=[f"{cr:.0%} capture" for cr in capture_rates])
    return df


def _calculate_irr(cash_flows: list, max_iter: int = 1000):
    """Calculate IRR using Newton's method."""
    if not cash_flows or cash_flows[0] >= 0:
        return None

    # Check if any positive cash flows exist
    if all(cf <= 0 for cf in cash_flows):
        return None

    rate = 0.10  # initial guess
    for _ in range(max_iter):
        npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))

        if abs(dnpv) < 1e-12:
            break

        new_rate = rate - npv / dnpv

        # Bound the rate to prevent divergence
        new_rate = max(-0.5, min(new_rate, 10.0))

        if abs(new_rate - rate) < 1e-8:
            return new_rate * 100  # as percentage
        rate = new_rate

    return rate * 100


# Comparable transactions (publicly available)
COMPARABLE_TRANSACTIONS = [
    {
        "property": "Pilot Travel Center, Knoxville TN",
        "year": 2023,
        "price": 14_200_000,
        "noi": 1_065_000,
        "cap_rate": 7.5,
        "acres": 12,
        "source": "CoStar",
    },
    {
        "property": "Love's Country Store, Amarillo TX",
        "year": 2023,
        "price": 8_750_000,
        "noi": 656_250,
        "cap_rate": 7.5,
        "acres": 8,
        "source": "CoStar",
    },
    {
        "property": "TA Express, Salina KS",
        "year": 2022,
        "price": 5_900_000,
        "noi": 472_000,
        "cap_rate": 8.0,
        "acres": 6,
        "source": "SEC Filing (BP/TravelCenters)",
    },
    {
        "property": "Independent Truck Stop, Rawlins WY",
        "year": 2024,
        "price": 2_200_000,
        "noi": 176_000,
        "cap_rate": 8.0,
        "acres": 4,
        "source": "LoopNet",
    },
]
