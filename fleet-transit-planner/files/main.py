"""
main.py — Streamlit dashboard for Fleet Transit Planning Optimization.
"""

import streamlit as st
import pandas as pd
from data import PORTS, SHIP_CLASSES
from optimizer import optimize_route, sensitivity_analysis
from charts import (
    chart_fuel_burn_curve,
    chart_speed_profile,
    chart_fuel_time_pareto,
    chart_sensitivity,
    chart_route_map,
)

st.set_page_config(
    page_title="Fleet Transit Planner",
    page_icon="⚓",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');

/* ── RESET & BASE ── */
html, body, [class*="css"], .stApp {
    background-color: #080f1a !important;
    color: #c8d8e8 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background-color: #050c17 !important;
    border-right: 1px solid #0d2137 !important;
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }

/* ── ALL INPUT WIDGETS - nuke the white ── */
/* Selectbox */
div[data-testid="stSelectbox"] > div > div {
    background-color: #0d2137 !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 3px !important;
    color: #c8a84b !important;
}
div[data-testid="stSelectbox"] > div > div:hover {
    border-color: #c8a84b !important;
}
div[data-testid="stSelectbox"] svg { fill: #c8a84b !important; }

/* Dropdown menu items */
div[data-baseweb="popover"] * {
    background-color: #0d2137 !important;
    color: #c8d8e8 !important;
    font-family: 'Rajdhani', sans-serif !important;
}
div[data-baseweb="popover"] li:hover {
    background-color: #1a3a5c !important;
    color: #c8a84b !important;
}

/* Number input */
div[data-testid="stNumberInput"] input {
    background-color: #0d2137 !important;
    border: 1px solid #1a3a5c !important;
    color: #c8a84b !important;
    font-family: 'Share Tech Mono', monospace !important;
    border-radius: 3px !important;
}
div[data-testid="stNumberInput"] button {
    background-color: #0d2137 !important;
    border: 1px solid #1a3a5c !important;
    color: #c8a84b !important;
}

/* Multiselect */
div[data-testid="stMultiSelect"] > div {
    background-color: #0d2137 !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 3px !important;
}
div[data-testid="stMultiSelect"] span {
    background-color: #1a3a5c !important;
    color: #c8a84b !important;
}
div[data-testid="stMultiSelect"] input { color: #c8d8e8 !important; }

/* Radio buttons */
div[data-testid="stRadio"] > div {
    background: transparent !important;
    gap: 6px !important;
}
div[data-testid="stRadio"] label {
    background-color: #0d2137 !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 3px !important;
    padding: 6px 12px !important;
    color: #7a9bbf !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background-color: #1a3a5c !important;
    border-color: #c8a84b !important;
    color: #c8a84b !important;
}
div[data-testid="stRadio"] input[type="radio"] { display: none !important; }

/* Slider */
div[data-testid="stSlider"] > div { padding: 0 4px; }
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background-color: #c8a84b !important;
    border-color: #c8a84b !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stTickBar"] {
    background: linear-gradient(to right, #1a3a5c, #c8a84b) !important;
}

/* ── LABELS ── */
label, .stSelectbox label, .stSlider label, .stRadio > label,
.stMultiSelect > label, .stNumberInput > label,
div[data-testid="stWidgetLabel"] {
    color: #3a6a9a !important;
    font-size: 0.68rem !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
}

/* Caption */
small, .stCaption { color: #1a3a5c !important; font-size: 0.65rem !important; }

/* ── HEADINGS ── */
h1 {
    color: #c8a84b !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
}
h2, h3 {
    color: #3a6a9a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #0d2137 !important;
    padding-bottom: 6px !important;
}

/* ── METRIC CARDS ── */
div[data-testid="metric-container"] {
    background: #0a1828 !important;
    border: 1px solid #0d2137 !important;
    border-top: 1px solid #c8a84b44 !important;
    border-radius: 2px !important;
    padding: 16px !important;
    position: relative !important;
}
div[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: #c8a84b;
    border-radius: 2px 0 0 2px;
}
div[data-testid="metric-container"] label {
    color: #3a6a9a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #c8d8e8 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.04em !important;
}

/* ── DATAFRAME ── */
div[data-testid="stDataFrame"] iframe,
div[data-testid="stDataFrame"] {
    background-color: #0a1828 !important;
    border: 1px solid #0d2137 !important;
    border-radius: 2px !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 1px solid #0d2137 !important;
    margin: 1.4rem 0 !important;
}

/* ── EXPANDER ── */
div[data-testid="stExpander"] {
    background: #0a1828 !important;
    border: 1px solid #0d2137 !important;
    border-radius: 2px !important;
}
div[data-testid="stExpander"] summary { color: #3a6a9a !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; background: #050c17; }
::-webkit-scrollbar-thumb { background: #1a3a5c; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    "<p style='font-family:Orbitron,sans-serif;color:#c8a84b;"
    "font-size:0.85rem;letter-spacing:0.12em;margin-bottom:4px'>⚓ FLEET TRANSIT</p>"
    "<p style='font-family:Share Tech Mono,monospace;color:#3a6a9a;"
    "font-size:0.62rem;letter-spacing:0.2em;margin-top:0'>PLANNING SYSTEM v1.0</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

ship_name  = st.sidebar.selectbox("Ship Class", list(SHIP_CLASSES.keys()))
ship_class = SHIP_CLASSES[ship_name]
st.sidebar.caption(ship_class["description"])

port_names  = sorted(PORTS.keys())
origin      = st.sidebar.selectbox("Origin Port", port_names,
                                    index=port_names.index("San Diego"))
destination = st.sidebar.selectbox("Destination Port", port_names,
                                    index=port_names.index("Yokosuka"))

st.sidebar.markdown("---")
mode = st.sidebar.radio(
    "Optimization Mode",
    ["Minimize Fuel (time constraint)", "Minimize Time (fuel constraint)"],
)
mode_key = "min_fuel" if "Fuel" in mode else "min_time"

if mode_key == "min_fuel":
    max_time_days    = st.sidebar.number_input("Max Transit Time (days)",
                                               min_value=1.0, max_value=60.0,
                                               value=20.0, step=0.5)
    constraint       = max_time_days * 24
    constraint_label = f"{max_time_days} days"
else:
    max_fuel_kgal    = st.sidebar.number_input("Max Fuel Budget (×1,000 gal)",
                                               min_value=10.0, max_value=2000.0,
                                               value=300.0, step=10.0)
    constraint       = max_fuel_kgal * 1000
    constraint_label = f"{max_fuel_kgal:.0f}k gal"

st.sidebar.markdown("---")
burn_multiplier = st.sidebar.slider(
    "Burn Rate Multiplier", 0.5, 2.0, 1.0, 0.05,
    help="Simulates weather, sea state, or load conditions",
)

st.sidebar.markdown("**Port Availability**")
unavailable     = st.sidebar.multiselect("Exclude Ports (waypoints)", port_names, default=[])
available_ports = [p for p in port_names if p not in unavailable]

st.sidebar.markdown("---")
sens_param = st.sidebar.radio(
    "Sensitivity Parameter",
    ["burn_multiplier", "constraint"],
    format_func=lambda x: "Burn Rate" if x == "burn_multiplier" else "Constraint Value",
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("⚓ Fuel & Time Constrained Transit Planning")
st.markdown(
    f"<span style='color:#3a6a9a;font-size:0.82rem;"
    f"font-family:Share Tech Mono,monospace;letter-spacing:0.06em'>"
    f"{ship_name} &nbsp;/&nbsp; {origin} → {destination} "
    f"&nbsp;/&nbsp; {mode} &nbsp;/&nbsp; {constraint_label}"
    f"</span>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Run optimization ───────────────────────────────────────────────────────────
if origin == destination:
    st.warning("Origin and destination must be different ports.")
    st.stop()

output = optimize_route(
    origin, destination, ship_class,
    mode=mode_key, constraint=constraint,
    available_ports=available_ports,
    burn_multiplier=burn_multiplier,
)

if output is None:
    st.error("No feasible route found. Try relaxing the constraint, adjusting the "
             "burn rate, or enabling more waypoint ports.")
    st.stop()

result, all_results = output

# ── Metrics ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
route_str  = " → ".join(result["path"])
refuel_str = ", ".join(result["refuel_stops"]) if result["refuel_stops"] else "None"

c1.metric("Route",          route_str if len(route_str) < 36 else f"{result['n_legs']} legs")
c2.metric("Total Distance", f"{result['total_distance_nm']:,} nm")
c3.metric("Total Fuel",     f"{result['total_fuel_gal']:,} gal")
c4.metric("Total Time",     f"{result['total_time_hr']} hrs ({result['total_time_hr']/24:.1f} d)")
c5.metric("Refuel Stops",   refuel_str)

st.markdown("---")

# ── Route map ──────────────────────────────────────────────────────────────────
st.subheader("Optimal Route Map")
st.altair_chart(chart_route_map(result), use_container_width=False)
st.markdown("---")

# ── Leg table ──────────────────────────────────────────────────────────────────
st.subheader("Leg-by-Leg Breakdown")
leg_df = pd.DataFrame(result["legs"])[
    ["from", "to", "distance_nm", "speed_kts", "fuel_gal", "time_hr"]
]
leg_df.columns = ["From", "To", "Distance (nm)", "Speed (kts)", "Fuel (gal)", "Time (hrs)"]
st.dataframe(
    leg_df.style.format({
        "Distance (nm)": "{:,}",
        "Fuel (gal)":    "{:,}",
        "Speed (kts)":   "{:.1f}",
        "Time (hrs)":    "{:.1f}",
    }),
    use_container_width=True,
)
st.markdown("---")

# ── Analysis charts ────────────────────────────────────────────────────────────
st.subheader("Analysis Charts")
a1, a2, a3 = st.columns(3)
with a1:
    st.altair_chart(chart_speed_profile(result), use_container_width=False)
with a2:
    first_dist = result["legs"][0]["distance_nm"]
    st.altair_chart(chart_fuel_time_pareto(ship_class, first_dist, burn_multiplier),
                    use_container_width=False)
with a3:
    st.altair_chart(chart_fuel_burn_curve(ship_class, burn_multiplier),
                    use_container_width=False)

st.markdown("---")

# ── Sensitivity ────────────────────────────────────────────────────────────────
st.subheader("Sensitivity Analysis")
sens_records = sensitivity_analysis(
    origin, destination, ship_class,
    mode=mode_key, constraint=constraint,
    param=sens_param,
    available_ports=available_ports,
    n_steps=12,
)
if any(r["feasible"] for r in sens_records):
    st.altair_chart(chart_sensitivity(sens_records, mode_key), use_container_width=False)
    with st.expander("View sensitivity data table"):
        st.dataframe(pd.DataFrame(sens_records), use_container_width=True)
else:
    st.warning("No feasible routes found across the sensitivity range.")

st.markdown("---")

# ── All feasible routes ────────────────────────────────────────────────────────
st.subheader("All Feasible Routes")
if all_results:
    routes_df = pd.DataFrame([{
        "Route":         " → ".join(r["path"]),
        "Distance (nm)": r["total_distance_nm"],
        "Fuel (gal)":    r["total_fuel_gal"],
        "Time (hrs)":    r["total_time_hr"],
        "Refuel Stops":  ", ".join(r["refuel_stops"]) or "None",
    } for r in sorted(all_results, key=lambda x: x["total_fuel_gal"])])
    st.dataframe(routes_df, use_container_width=True)
else:
    st.info("No alternative feasible routes found.")

st.markdown("---")
st.caption("Fleet Transit Planning · Operations Research · USNA · Streamlit + Altair")
