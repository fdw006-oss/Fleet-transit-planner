"""
charts.py — Altair visualizations matched to the futuristic dark theme.
"""

import altair as alt
import pandas as pd
import numpy as np
from data import PORTS
from fuel_model import FuelModel

BG      = "#080f1a"
PANEL   = "#0a1828"
GRID    = "#0d2137"
GOLD    = "#c8a84b"
STEEL   = "#2a5a8a"
DIM     = "#3a6a9a"
TEXT    = "#c8d8e8"
RED     = "#c0392b"
GREEN   = "#1a6b4a"
MONO    = "Share Tech Mono, monospace"


def _cfg(chart, w, h, title):
    return (
        chart
        .properties(title=title, width=w, height=h)
        .configure_view(fill=PANEL, stroke=GRID, strokeWidth=1)
        .configure_axis(
            gridColor=GRID, gridOpacity=1,
            labelColor=DIM, titleColor=DIM,
            tickColor=GRID, domainColor=GRID,
            labelFont=MONO, titleFont=MONO,
            labelFontSize=10, titleFontSize=10,
            labelPadding=6,
        )
        .configure_title(
            color=GOLD, fontSize=11, font=MONO,
            fontWeight="normal", anchor="start", offset=10,
            subtitleColor=DIM,
        )
        .configure_legend(
            labelColor=TEXT, titleColor=GOLD,
            labelFont=MONO, titleFont=MONO,
            labelFontSize=10, titleFontSize=10,
            strokeColor=GRID, padding=8,
            fillColor=PANEL,
        )
    )


def chart_fuel_burn_curve(ship_class: dict, burn_multiplier: float = 1.0):
    fm = FuelModel(ship_class)
    speeds = np.linspace(fm.min_speed, fm.max_speed, 80)
    rates  = [fm.burn_rate(s, burn_multiplier) for s in speeds]
    df = pd.DataFrame({"Speed (kts)": np.round(speeds, 1),
                        "Burn Rate (gal/hr)": np.round(rates, 1)})

    area = alt.Chart(df).mark_area(
        color=GOLD, opacity=0.08, line=False
    ).encode(
        x=alt.X("Speed (kts):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Burn Rate (gal/hr):Q", scale=alt.Scale(zero=False)),
    )
    line = alt.Chart(df).mark_line(color=GOLD, strokeWidth=2).encode(
        x=alt.X("Speed (kts):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Burn Rate (gal/hr):Q", scale=alt.Scale(zero=False)),
        tooltip=["Speed (kts)", "Burn Rate (gal/hr)"],
    )
    return _cfg(area + line, 310, 200, "// FUEL BURN CURVE")


def chart_speed_profile(result: dict):
    rows = [{"Leg": f"{l['from'][:3]}›{l['to'][:3]}",
             "Speed (kts)": l["speed_kts"],
             "Distance (nm)": l["distance_nm"]}
            for l in result["legs"]]
    df = pd.DataFrame(rows)

    bars = alt.Chart(df).mark_bar(
        color=STEEL, stroke=GOLD, strokeWidth=0.6,
        cornerRadiusTopLeft=2, cornerRadiusTopRight=2,
    ).encode(
        x=alt.X("Leg:N", sort=None, axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("Speed (kts):Q", scale=alt.Scale(zero=False)),
        tooltip=["Leg", "Speed (kts)", "Distance (nm)"],
    )
    return _cfg(bars, 310, 200, "// SPEED PROFILE PER LEG")


def chart_fuel_time_pareto(ship_class: dict, distance_nm: float,
                            burn_multiplier: float = 1.0):
    fm = FuelModel(ship_class)
    speeds, fuels, times = fm.pareto_frontier(distance_nm, burn_multiplier)
    df = pd.DataFrame({
        "Time (hrs)":  np.round(times, 1),
        "Fuel (gal)":  np.round(fuels).astype(int),
        "Speed (kts)": np.round(speeds, 1),
    })

    line = alt.Chart(df).mark_line(
        color=STEEL, strokeWidth=1.5, strokeDash=[3, 2]
    ).encode(
        x=alt.X("Time (hrs):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Fuel (gal):Q", scale=alt.Scale(zero=False)),
    )
    pts = alt.Chart(df).mark_circle(color=GOLD, size=45, opacity=0.9).encode(
        x="Time (hrs):Q", y="Fuel (gal):Q",
        tooltip=["Speed (kts)", "Time (hrs)", "Fuel (gal)"],
    )
    return _cfg(line + pts, 310, 200,
                f"// FUEL vs TIME  [{distance_nm:,} nm leg]")


def chart_sensitivity(sensitivity_records: list, mode: str):
    df = pd.DataFrame(sensitivity_records)
    df = df[df["feasible"]]
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="NO DATA")

    y_field = "total_fuel_gal" if mode == "min_fuel" else "total_time_hr"
    y_label = "Total Fuel (gal)" if mode == "min_fuel" else "Total Time (hrs)"
    x_label = df["param_label"].iloc[0]
    df = df.rename(columns={"param_value": x_label, y_field: y_label})

    area = alt.Chart(df).mark_area(color=GOLD, opacity=0.07).encode(
        x=f"{x_label}:Q",
        y=alt.Y(f"{y_label}:Q", scale=alt.Scale(zero=False)),
    )
    line = alt.Chart(df).mark_line(
        color=GOLD, strokeWidth=2,
        point=alt.OverlayMarkDef(color=GOLD, size=40),
    ).encode(
        x=alt.X(f"{x_label}:Q"),
        y=alt.Y(f"{y_label}:Q", scale=alt.Scale(zero=False)),
        tooltip=[x_label, y_label],
    )
    return _cfg(area + line, 690, 210, "// SENSITIVITY ANALYSIS")


def chart_route_map(result: dict):
    port_df = pd.DataFrame([
        {"Port": k, "lat": v["lat"], "lon": v["lon"]}
        for k, v in PORTS.items()
    ])

    route_path = result["path"]
    route_point_df = pd.DataFrame([
        {"Port": p,
         "lat": PORTS[p]["lat"], "lon": PORTS[p]["lon"],
         "role": "Origin" if p == route_path[0]
                 else ("Destination" if p == route_path[-1] else "Waypoint")}
        for p in route_path
    ])
    edge_df = pd.DataFrame([{
        "from": l["from"], "to": l["to"],
        "lat1": PORTS[l["from"]]["lat"], "lon1": PORTS[l["from"]]["lon"],
        "lat2": PORTS[l["to"]]["lat"],   "lon2": PORTS[l["to"]]["lon"],
        "speed_kts": l["speed_kts"], "fuel_gal": l["fuel_gal"],
        "dist_nm": l["distance_nm"],
    } for l in result["legs"]])

    # Background port grid dots
    bg = alt.Chart(port_df).mark_circle(size=40, opacity=0.2, color=DIM).encode(
        x=alt.X("lon:Q", scale=alt.Scale(domain=[-180, 180]),
                axis=alt.Axis(title="LON", tickCount=8, labelFontSize=9)),
        y=alt.Y("lat:Q", scale=alt.Scale(domain=[-55, 70]),
                axis=alt.Axis(title="LAT", tickCount=6, labelFontSize=9)),
        tooltip=["Port:N"],
    )

    # Glow effect: thick faded line under the gold line
    glow = alt.Chart(edge_df).mark_rule(
        strokeWidth=8, color=GOLD, opacity=0.12
    ).encode(
        x="lon1:Q", y="lat1:Q", x2="lon2:Q", y2="lat2:Q",
    )

    lines = alt.Chart(edge_df).mark_rule(
        strokeWidth=2, color=GOLD, opacity=0.95
    ).encode(
        x="lon1:Q", y="lat1:Q", x2="lon2:Q", y2="lat2:Q",
        tooltip=["from:N", "to:N",
                 alt.Tooltip("dist_nm:Q", title="Dist (nm)"),
                 alt.Tooltip("speed_kts:Q", title="Speed (kts)"),
                 alt.Tooltip("fuel_gal:Q", title="Fuel (gal)")],
    )

    color_scale = alt.Scale(
        domain=["Origin", "Destination", "Waypoint"],
        range=[RED, GREEN, GOLD],
    )

    # Outer ring (glow)
    ring = alt.Chart(route_point_df).mark_circle(
        size=320, opacity=0.12, stroke=None,
    ).encode(
        x="lon:Q", y="lat:Q",
        color=alt.Color("role:N", scale=color_scale, legend=None),
    )

    pts = alt.Chart(route_point_df).mark_circle(
        size=130, stroke=BG, strokeWidth=1.5
    ).encode(
        x="lon:Q", y="lat:Q",
        color=alt.Color("role:N", scale=color_scale,
                        legend=alt.Legend(title="PORT ROLE")),
        tooltip=["Port:N", "role:N"],
    )

    labels = alt.Chart(route_point_df).mark_text(
        align="left", dx=10, dy=-4,
        fontSize=10, font=MONO, color=TEXT,
    ).encode(x="lon:Q", y="lat:Q", text="Port:N")

    return _cfg(
        bg + glow + lines + ring + pts + labels,
        710, 370, "// OPTIMAL ROUTE MAP",
    )
