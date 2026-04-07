"""
fuel_model.py — Fuel burn rate vs speed model for ship classes.
"""

import numpy as np


class FuelModel:
    """
    Models fuel consumption as a cubic function of speed:
        burn_rate (gal/hr) = a * speed^3 + b
    """

    def __init__(self, ship_class: dict):
        self.a = ship_class["fuel_a"]
        self.b = ship_class["fuel_b"]
        self.min_speed = ship_class["min_speed"]
        self.max_speed = ship_class["max_speed"]

    def burn_rate(self, speed: float, burn_multiplier: float = 1.0) -> float:
        """Gallons per hour at a given speed (knots)."""
        return burn_multiplier * (self.a * speed ** 3 + self.b)

    def fuel_for_leg(self, distance_nm: float, speed: float,
                     burn_multiplier: float = 1.0) -> float:
        """Total gallons consumed on a leg of given distance at given speed."""
        hours = self.time_for_leg(distance_nm, speed)
        return self.burn_rate(speed, burn_multiplier) * hours

    def time_for_leg(self, distance_nm: float, speed: float) -> float:
        """Hours to travel a leg at given speed."""
        if speed <= 0:
            return float("inf")
        return distance_nm / speed

    def pareto_frontier(self, distance_nm: float, burn_multiplier: float = 1.0,
                        n_points: int = 40):
        """
        Returns arrays of (speed, fuel, time) across the ship's speed range.
        Used to visualize the fuel vs time tradeoff for a single leg.
        """
        speeds = np.linspace(self.min_speed, self.max_speed, n_points)
        fuels = [self.fuel_for_leg(distance_nm, s, burn_multiplier) for s in speeds]
        times = [self.time_for_leg(distance_nm, s) for s in speeds]
        return speeds, fuels, times
