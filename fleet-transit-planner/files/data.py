"""
data.py — Sample port, route, and ship class data for fleet transit planning.
"""

# Ports with name, lat/lon, and whether they can refuel
PORTS = {
    "San Diego":     {"lat": 32.72, "lon": -117.17, "refuel": True},
    "Pearl Harbor":  {"lat": 21.35, "lon": -157.97, "refuel": True},
    "Guam":          {"lat": 13.44, "lon": 144.65,  "refuel": True},
    "Yokosuka":      {"lat": 35.29, "lon": 139.67,  "refuel": True},
    "Singapore":     {"lat": 1.26,  "lon": 103.82,  "refuel": True},
    "Sydney":        {"lat": -33.86,"lon": 151.21,  "refuel": True},
    "Anchorage":     {"lat": 61.22, "lon": -149.90, "refuel": False},
    "Bremerton":     {"lat": 47.57, "lon": -122.63, "refuel": True},
    "Darwin":        {"lat": -12.46,"lon": 130.84,  "refuel": False},
    "Honolulu":      {"lat": 21.31, "lon": -157.86, "refuel": True},
}

# Distances in nautical miles between port pairs (symmetric)
# Only direct legs are listed; others require waypoints
DISTANCES = {
    ("San Diego",    "Pearl Harbor"):  2224,
    ("San Diego",    "Anchorage"):     1830,
    ("San Diego",    "Bremerton"):     1050,
    ("Pearl Harbor", "Guam"):          3300,
    ("Pearl Harbor", "Yokosuka"):      3450,
    ("Pearl Harbor", "Honolulu"):      20,
    ("Pearl Harbor", "Anchorage"):     2090,
    ("Guam",         "Yokosuka"):      1300,
    ("Guam",         "Singapore"):     2400,
    ("Guam",         "Darwin"):        1900,
    ("Guam",         "Sydney"):        3200,
    ("Yokosuka",     "Singapore"):     3300,
    ("Yokosuka",     "Bremerton"):     4250,
    ("Singapore",    "Darwin"):        1850,
    ("Singapore",    "Sydney"):        3900,
    ("Darwin",       "Sydney"):        2100,
    ("Bremerton",    "Anchorage"):     1400,
    ("Honolulu",     "Guam"):          3320,
}

# Ship classes with speed range (knots) and fuel burn curve coefficients
# burn_rate (gallons/hour) = a * speed^3 + b
SHIP_CLASSES = {
    "Destroyer (DDG)": {
        "min_speed": 8,
        "max_speed": 30,
        "fuel_a": 0.018,   # cubic coefficient
        "fuel_b": 120,     # base hotel load (gallons/hr)
        "fuel_capacity": 500000,  # gallons
        "description": "Fast, high fuel consumption at speed"
    },
    "Cruiser (CG)": {
        "min_speed": 6,
        "max_speed": 27,
        "fuel_a": 0.025,
        "fuel_b": 180,
        "fuel_capacity": 700000,
        "description": "Balanced speed and endurance"
    },
    "Amphibious (LHD)": {
        "min_speed": 5,
        "max_speed": 22,
        "fuel_a": 0.045,
        "fuel_b": 300,
        "fuel_capacity": 1200000,
        "description": "Large capacity, slower and fuel-heavy"
    },
}
