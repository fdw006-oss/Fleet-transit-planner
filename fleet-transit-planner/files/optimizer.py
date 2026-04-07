"""
optimizer.py — Route optimization for fuel-min and time-min problems.
"""

import numpy as np
from scipy.optimize import minimize_scalar
from network import build_graph, get_all_paths, path_distance, get_refuel_stops
from fuel_model import FuelModel


def optimal_speed_min_fuel(distance_nm: float, max_time_hr: float,
                           fuel_model: FuelModel,
                           burn_multiplier: float = 1.0) -> float:
    """
    For a single leg, find the speed that minimizes fuel subject to
    arriving within max_time_hr. Returns the optimal speed in knots.
    """
    min_speed = fuel_model.min_speed
    max_speed = fuel_model.max_speed

    # Minimum time physically possible
    min_possible_time = distance_nm / max_speed
    if max_time_hr < min_possible_time:
        # Can't make it even at max speed — go as fast as possible
        return max_speed

    # Slowest speed that meets the time constraint
    slowest_feasible = distance_nm / max_time_hr
    slowest_feasible = max(slowest_feasible, min_speed)

    # Lower speed = less fuel (cubic), so use slowest feasible speed
    return round(min(slowest_feasible, max_speed), 2)


def optimal_speed_min_time(distance_nm: float, max_fuel: float,
                           fuel_model: FuelModel,
                           burn_multiplier: float = 1.0) -> float:
    """
    For a single leg, find the speed that minimizes time subject to
    not exceeding max_fuel. Returns the optimal speed in knots.
    """
    min_speed = fuel_model.min_speed
    max_speed = fuel_model.max_speed

    # Check if max speed is feasible
    fuel_at_max = fuel_model.fuel_for_leg(distance_nm, max_speed, burn_multiplier)
    if fuel_at_max <= max_fuel:
        return max_speed

    # Binary search for fastest speed within fuel budget
    lo, hi = min_speed, max_speed
    for _ in range(50):
        mid = (lo + hi) / 2
        if fuel_model.fuel_for_leg(distance_nm, mid, burn_multiplier) <= max_fuel:
            lo = mid
        else:
            hi = mid
    return round(lo, 2)


def evaluate_path(path: list, G, fuel_model: FuelModel,
                  mode: str, constraint: float,
                  burn_multiplier: float = 1.0) -> dict:
    """
    Given a path (list of ports), compute optimal speeds per leg,
    total fuel, and total time under either:
      mode='min_fuel'  with constraint = max_time_hr
      mode='min_time'  with constraint = max_fuel (gallons)
    Returns a dict with results, or None if infeasible.
    """
    legs = []
    total_fuel = 0.0
    total_time = 0.0
    n_legs = len(path) - 1

    for i in range(n_legs):
        a, b = path[i], path[i + 1]
        dist = G[a][b]["distance"]

        if mode == "min_fuel":
            # Distribute time budget evenly across legs
            leg_time_budget = constraint / n_legs
            speed = optimal_speed_min_fuel(dist, leg_time_budget, fuel_model,
                                           burn_multiplier)
        else:
            # Distribute fuel budget evenly across legs
            leg_fuel_budget = constraint / n_legs
            speed = optimal_speed_min_time(dist, leg_fuel_budget, fuel_model,
                                           burn_multiplier)

        fuel = fuel_model.fuel_for_leg(dist, speed, burn_multiplier)
        time = fuel_model.time_for_leg(dist, speed)

        legs.append({
            "from": a,
            "to": b,
            "distance_nm": dist,
            "speed_kts": speed,
            "fuel_gal": round(fuel),
            "time_hr": round(time, 1),
        })
        total_fuel += fuel
        total_time += time

    # Feasibility check
    if mode == "min_fuel" and total_time > constraint * 1.01:
        return None
    if mode == "min_time" and total_fuel > constraint * 1.01:
        return None

    return {
        "path": path,
        "legs": legs,
        "total_fuel_gal": round(total_fuel),
        "total_time_hr": round(total_time, 1),
        "total_distance_nm": round(sum(l["distance_nm"] for l in legs)),
        "refuel_stops": get_refuel_stops(path),
        "n_legs": n_legs,
    }


def optimize_route(origin: str, destination: str, ship_class: dict,
                   mode: str, constraint: float,
                   available_ports: list = None,
                   burn_multiplier: float = 1.0) -> dict:
    """
    Find the optimal route between origin and destination.
    mode: 'min_fuel' or 'min_time'
    constraint: max_time_hr (min_fuel) or max_fuel_gal (min_time)
    Returns best result dict or None if no feasible route found.
    """
    G = build_graph(available_ports)
    fuel_model = FuelModel(ship_class)

    if origin not in G or destination not in G:
        return None

    paths = get_all_paths(G, origin, destination)
    if not paths:
        return None

    best = None
    all_results = []

    for path in paths:
        result = evaluate_path(path, G, fuel_model, mode, constraint,
                               burn_multiplier)
        if result is None:
            continue
        all_results.append(result)

        if best is None:
            best = result
        elif mode == "min_fuel" and result["total_fuel_gal"] < best["total_fuel_gal"]:
            best = result
        elif mode == "min_time" and result["total_time_hr"] < best["total_time_hr"]:
            best = result

    return best, all_results


def sensitivity_analysis(origin: str, destination: str, ship_class: dict,
                          mode: str, constraint: float,
                          param: str, available_ports: list = None,
                          n_steps: int = 10) -> list:
    """
    Vary one parameter across a range and return results.
    param options: 'burn_multiplier', 'constraint'
    Returns list of dicts with param value + result metrics.
    """
    G = build_graph(available_ports)
    fuel_model = FuelModel(ship_class)
    paths = get_all_paths(G, origin, destination)

    if param == "burn_multiplier":
        values = np.linspace(0.5, 2.0, n_steps)
        param_label = "Burn Rate Multiplier"
    else:
        # vary the constraint ±50%
        values = np.linspace(constraint * 0.5, constraint * 1.5, n_steps)
        param_label = "Constraint Value"

    records = []
    for val in values:
        bm = val if param == "burn_multiplier" else 1.0
        con = constraint if param == "burn_multiplier" else val

        best_fuel = None
        best_time = None

        for path in paths:
            result = evaluate_path(path, G, fuel_model, mode, con, bm)
            if result is None:
                continue
            if best_fuel is None or result["total_fuel_gal"] < best_fuel:
                best_fuel = result["total_fuel_gal"]
            if best_time is None or result["total_time_hr"] < best_time:
                best_time = result["total_time_hr"]

        records.append({
            "param_label": param_label,
            "param_value": round(val, 3),
            "total_fuel_gal": best_fuel,
            "total_time_hr": best_time,
            "feasible": best_fuel is not None,
        })

    return records
