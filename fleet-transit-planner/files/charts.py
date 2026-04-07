"""
charts.py — All Altair visualizations for the fleet transit planner.
Palette: deep navy + gold, consistent across all charts.
"""

import altair as alt
import pandas as pd
import numpy as np
from data import PORTS
from fuel_model import FuelModel

# ── Palette ────────────────────────────────────────────────────────────────────
BG        = "#0b1f3a"   # deep navy background
BG_LIGHT  = "#112b50"   # slightly lighter navy for chart areas
GRID      = "#1a3a5c"   # subtle grid lines
GOLD      = "#c8a84b"   # primary gold accent
GOLD_SOFT = "#e8c96b"   # lighter gold for hover/labels
STEEL     = "#4a7fb5"   # muted steel blue for secondary data
WHITE     = "#e8edf2"   # off-white text
DIM       = "#7a9bbf"   # dimmed text / secondary labels
RED       = "#c0392b"   # origin marker
GREEN     = "#27ae60"   # destination marker

ALT_CONFIG = {
    "view":   {"fill": BG_LIGHT, "stroke": GRID, "strokeWidth": 1},
    "axis":   {"gridColor": GRID, "labelColor": DIM, "titleColor": WHITE,
               "tickColor": GRID, "domainColor": GRID,
               "labelFont": "Georgia", "titleFont": "Georgia"},
    "title":  {"color": GOLD, "fontSize": 13, "font": "Georgia",
               "fontWeight": "normal", "anchor": "start", "offset": 8},
    "legend": {"labelColor": WHITE, "titleColor": GOLD,
               "labelFont": "Georgia", "titleFont": "Georgia",
               "strokeColor": GRID, "padding": 6},
}

def _apply(chart):
    return (chart
        .configure_view(**ALT_CONFIG["view"])
        .configure_axis(**ALT_CONFIG["axis"])
        .configure_title(**ALT_CONFIG["title"])
        .configure_legend(**ALT_CONFIG["legend"])
    )


def chart_fuel_burn_curve(ship_class: dict, burn_multiplier: float = 1.0) -> alt.Chart:
    """Line chart of burn rate (gal/hr) vs speed (knots)."""
    fm = FuelModel(ship_class)
    speeds = np.linspace(fm.min_speed, fm.max_speed, 80)
    rates  = [fm.burn_rate(s, burn_multiplier) for s in speeds]

    df = pd.DataFrame({"Speed (kts)": np.round(speeds, 1),
                       "Burn Rate (gal/hr)": np.round(rates, 1)})

    area = (alt.Chart(df)
        .mark_area(color=GOLD, opacity=0.12, line=False)
        .encode(x="Speed (kts):Q", y=alt.Y("Burn Rate (gal/hr):Q", scale=alt.Scale(zero=False)))
    )
    line = (alt.Chart(df)
        .mark_line(color=GOLD, strokeWidth=2.5)
        .encode(
            x=alt.X("Speed (kts):Q", scale=alt.Scale(zero=False)),
            y=alt.Y("Burn Rate (gal/hr):Q", scale=alt.Scale(zero=False)),
            tooltip=["Speed (kts)", "Burn Rate (gal/hr)"],
        )
    )
    return _apply((area + line).properties(title="Fuel Burn Curve", width=310, height=210))


def chart_speed_profile(result: dict) -> alt.Chart:
    """Bar chart of optimal speed per leg."""
    rows = [{"Leg": f"{l['from'][:3]}→{l['to'][:3]}",
             "Speed (kts)": l["speed_kts"],
             "Distance (nm)": l["distance_nm"]}
            for l in result["legs"]]
    df = pd.DataFrame(rows)

    bars = (alt.Chart(df)
        .mark_bar(color=STEEL, stroke=GOLD, strokeWidth=0.8,
                  cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Leg:N", sort=None, axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("Speed (kts):Q", scale=alt.Scale(zero=False)),
            tooltip=["Leg", "Speed (kts)", "Distance (nm)"],
        )
    )
    return _apply(bars.properties(title="Optimal Speed per Leg", width=310, height=210))


def chart_fuel_time_pareto(ship_class: dict, distance_nm: float,
                            burn_multiplier: float = 1.0) -> alt.Chart:
    """Line + points showing fuel vs time tradeoff."""
    fm = FuelModel(ship_class)
    speeds, fuels, times = fm.pareto_frontier(distance_nm, burn_multiplier)

    df = pd.DataFrame({
        "Time (hrs)":  np.round(times, 1),
        "Fuel (gal)":  np.round(fuels).astype(int),
        "Speed (kts)": np.round(speeds, 1),
    })

    line = (alt.Chart(df)
        .mark_line(color=STEEL, strokeWidth=2, strokeDash=[4, 2])
        .encode(x=alt.X("Time (hrs):Q", scale=alt.Scale(zero=False)),
                y=alt.Y("Fuel (gal):Q", scale=alt.Scale(zero=False)))
    )
    pts = (alt.Chart(df)
        .mark_circle(color=GOLD, size=50, opacity=0.85)
        .encode(
            x="Time (hrs):Q", y="Fuel (gal):Q",
            tooltip=["Speed (kts)", "Time (hrs)", "Fuel (gal)"],
        )
    )
    return _apply((line + pts).properties(
        title=f"Fuel vs Time Tradeoff ({distance_nm:,} nm leg)",
        width=310, height=210))


def chart_sensitivity(sensitivity_records: list, mode: str) -> alt.Chart:
    """Line chart of sensitivity analysis results."""
    df = pd.DataFrame(sensitivity_records)
    df = df[df["feasible"]]
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="No feasible data")

    y_field = "total_fuel_gal" if mode == "min_fuel" else "total_time_hr"
    y_label = "Total Fuel (gal)"  if mode == "min_fuel" else "Total Time (hrs)"
    x_label = df["param_label"].iloc[0]

    df = df.rename(columns={"param_value": x_label, y_field: y_label})

    area = (alt.Chart(df)
        .mark_area(color=GOLD, opacity=0.10, line=False)
        .encode(x=f"{x_label}:Q", y=alt.Y(f"{y_label}:Q", scale=alt.Scale(zero=False)))
    )
    line = (alt.Chart(df)
        .mark_line(color=GOLD, strokeWidth=2.5,
                   point=alt.OverlayMarkDef(color=GOLD, size=50))
        .encode(
            x=alt.X(f"{x_label}:Q"),
            y=alt.Y(f"{y_label}:Q", scale=alt.Scale(zero=False)),
            tooltip=[x_label, y_label],
        )
    )
    return _apply((area + line).properties(title="Sensitivity Analysis", width=680, height=220))


def chart_route_map(result: dict) -> alt.Chart:
    """
    Lat/lon scatter map: all ports in dim steel, route in gold lines,
    origin/destination/waypoints color-coded.
    """
    port_df = pd.DataFrame([
        {"Port": k, "lat": v["lat"], "lon": v["lon"], "refuel": v["refuel"]}
        for k, v in PORTS.items()
    ])

    route_path = result["path"]

    route_point_df = pd.DataFrame([
        {"Port": p,
         "lat": PORTS[p]["lat"],
         "lon": PORTS[p]["lon"],
         "role": "Origin"      if p == route_path[0]
                 else ("Destination" if p == route_path[-1] else "Waypoint")}
        for p in route_path
    ])

    edge_df = pd.DataFrame([{
        "from": l["from"], "to": l["to"],
        "lat1": PORTS[l["from"]]["lat"], "lon1": PORTS[l["from"]]["lon"],
        "lat2": PORTS[l["to"]]["lat"],   "lon2": PORTS[l["to"]]["lon"],
        "speed_kts": l["speed_kts"],
        "fuel_gal":  l["fuel_gal"],
        "dist_nm":   l["distance_nm"],
    } for l in result["legs"]])

    bg = (alt.Chart(port_df)
        .mark_circle(size=55, opacity=0.35, color=STEEL)
        .encode(
            x=alt.X("lon:Q", scale=alt.Scale(domain=[-180, 180]),
                    axis=alt.Axis(title="Longitude", tickCount=8)),
            y=alt.Y("lat:Q", scale=alt.Scale(domain=[-55, 70]),
                    axis=alt.Axis(title="Latitude",  tickCount=6)),
            tooltip=["Port:N"],
        )
    )

    lines = (alt.Chart(edge_df)
        .mark_rule(strokeWidth=3, color=GOLD, opacity=0.9)
        .encode(
            x="lon1:Q", y="lat1:Q", x2="lon2:Q", y2="lat2:Q",
            tooltip=["from:N", "to:N",
                     alt.Tooltip("dist_nm:Q", title="Distance (nm)"),
                     alt.Tooltip("speed_kts:Q", title="Speed (kts)"),
                     alt.Tooltip("fuel_gal:Q", title="Fuel (gal)")],
        )
    )

    color_scale = alt.Scale(
        domain=["Origin", "Destination", "Waypoint"],
        range=[RED, GREEN, GOLD_SOFT],
    )
    pts = (alt.Chart(route_point_df)
        .mark_circle(size=170, stroke=WHITE, strokeWidth=1.2)
        .encode(
            x="lon:Q", y="lat:Q",
            color=alt.Color("role:N", scale=color_scale,
                            legend=alt.Legend(title="Port Role")),
            tooltip=["Port:N", "role:N"],
        )
    )

    labels = (alt.Chart(route_point_df)
        .mark_text(align="left", dx=9, dy=-5, fontSize=11,
                   color=WHITE, font="Georgia")
        .encode(x="lon:Q", y="lat:Q", text="Port:N")
    )

    return _apply(
        (bg + lines + pts + labels)
        .properties(title="Optimal Route Map", width=700, height=370)
    )
