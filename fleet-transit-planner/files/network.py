"""
network.py — Graph/network model of ports and routes using NetworkX.
"""

import networkx as nx
from data import PORTS, DISTANCES


def build_graph(available_ports: list = None) -> nx.Graph:
    """
    Build an undirected NetworkX graph from port and distance data.
    Optionally filter to only include a subset of ports.
    """
    G = nx.Graph()

    # Add port nodes
    for name, info in PORTS.items():
        if available_ports is None or name in available_ports:
            G.add_node(name, **info)

    # Add edges for each direct leg
    for (port_a, port_b), dist in DISTANCES.items():
        a_ok = available_ports is None or port_a in available_ports
        b_ok = available_ports is None or port_b in available_ports
        if a_ok and b_ok:
            G.add_edge(port_a, port_b, distance=dist)

    return G


def get_all_paths(G: nx.Graph, origin: str, destination: str) -> list:
    """Return all simple paths between origin and destination."""
    try:
        return list(nx.all_simple_paths(G, origin, destination, cutoff=5))
    except nx.NetworkXNoPath:
        return []


def path_distance(G: nx.Graph, path: list) -> float:
    """Total nautical miles for a given path (list of port names)."""
    total = 0.0
    for i in range(len(path) - 1):
        total += G[path[i]][path[i + 1]]["distance"]
    return total


def get_refuel_stops(path: list) -> list:
    """Return ports in the path (excluding origin/destination) that can refuel."""
    refuel = []
    for port in path[1:-1]:
        if PORTS.get(port, {}).get("refuel", False):
            refuel.append(port)
    return refuel
