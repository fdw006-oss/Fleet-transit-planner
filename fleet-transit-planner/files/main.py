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
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600&family=Share+Tech+Mono&display=swap');

/* ── Global ── */
html, body, .stApp { background-color: #0b1f3a; color: #e8edf2; }
* { font-family: 'EB Garamond', Georgia, serif; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #071528;
    border-right: 1px solid #1a3a5c;
}
section[data-testid="stSidebar"] * { color: #7a9bbf !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #c8a84b !important; }

/* ── Main headings ── */
h1 { color: #c8a84b !important; font-size: 1.9rem !important; letter-spacing: 0.03em; }
h2, h3 { color: #c8a84b !important; font-size: 1.2rem !important;
          letter-spacing: 0.04em; text-transform: uppercase; }

/* ── Metric cards ── */
div[data-testid="metric-container"] {
    background: #112b50;
    border: 1px solid #1a3a5c;
    border-top: 2px solid #c8a84b;
    border-radius: 4px;
    padding: 14px 16px;
}
div[data-testid="metric-container"] label {
    color: #7a9bbf !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #e8c96b !important;
    font-size: 1.15rem !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* ── Dataframe ── */
div[data-testid="stDataFrame"] { border: 1px solid #1a3a5c; border-radius: 4px; }

/* ── Divider ── */
hr { border-color: #1a3a5c !important; margin: 1.2rem 0; }

/* ── Selectbox / radio / slider labels ── */
.stSelectbox label, .stSlider label, .stRadio label,
.stMultiSelect label, .stNumberInput label {
    color: #7a9bbf !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Buttons ── */
.stButton > button {
    background: #112b50;
    border: 1px solid #c8a84b;
    color: #c8a84b;
    border-radius: 3px;
}

/* ── Caption ── */
.stCaption { color: #1a3a5c !important; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("## ⚓ Fleet Transit Planner")
st.sidebar.markdown("---")

ship_name = st.sidebar.selectbox("Ship Class", list(SHIP_CLASSES.keys()))
ship_class = SHIP_CLASSES[ship_name]
st.sidebar.caption(ship_class["description"])

port_names = sorted(PORTS.keys())
origin      = st.sidebar.selectbox("Origin Port", port_names,
                                    index=port_names.index("San Diego"))
destination = st.sidebar.selectbox("Destination Port", port_names,
                                    index=port_names.index("Yokosuka"))

st.sidebar.markdown("---")
mode = st.sidebar.radio("Optimization Mode",
                         ["Minimize Fuel (time constraint)",
                          "Minimize Time (fuel constraint)"])
mode_key = "min_fuel" if "Fuel" in mode else "min_time"

if mode_key == "min_fuel":
    max_time_days = st.sidebar.number_input("Max Transit Time (days)",
                                             min_value=1.0, max_value=60.0,
                                             value=20.0, step=0.5)
    constraint       = max_time_days * 24
    constraint_label = f"{max_time_days} days"
else:
    max_fuel_kgal = st.sidebar.number_input("Max Fuel Budget (×1,000 gal)",
                                             min_value=10.0, max_value=2000.0,
                                             value=300.0, step=10.0)
    constraint       = max_fuel_kgal * 1000
    constraint_label = f"{max_fuel_kgal:.0f}k gal"

st.sidebar.markdown("---")
burn_multiplier = st.sidebar.slider("Burn Rate Multiplier", 0.5, 2.0, 1.0, 0.05,
                                     help="Simulates weather, sea state, or load conditions")

st.sidebar.markdown("**Port Availability**")
unavailable    = st.sidebar.multiselect("Exclude Ports (waypoints)", port_names, default=[])
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
    f"<span style='color:#7a9bbf;font-size:0.9rem'>"
    f"**{ship_name}** &nbsp;·&nbsp; {origin} → {destination} "
    f"&nbsp;·&nbsp; *{mode}* &nbsp;·&nbsp; Constraint: {constraint_label}"
    f"</span>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Optimization ───────────────────────────────────────────────────────────────
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

c1.metric("Route",          route_str if len(route_str) < 38 else f"{result['n_legs']} legs")
c2.metric("Total Distance", f"{result['total_distance_nm']:,} nm")
c3.metric("Total Fuel",     f"{result['total_fuel_gal']:,} gal")
c4.metric("Total Time",     f"{result['total_time_hr']} hrs  "
                             f"({result['total_time_hr']/24:.1f} days)")
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
        "Route":          " → ".join(r["path"]),
        "Distance (nm)":  r["total_distance_nm"],
        "Fuel (gal)":     r["total_fuel_gal"],
        "Time (hrs)":     r["total_time_hr"],
        "Refuel Stops":   ", ".join(r["refuel_stops"]) or "None",
    } for r in sorted(all_results, key=lambda x: x["total_fuel_gal"])])
    st.dataframe(routes_df, use_container_width=True)
else:
    st.info("No alternative feasible routes found.")

st.markdown("---")
st.caption("Fleet Transit Planning · Operations Research · USNA · Streamlit + Altair")
