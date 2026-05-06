"""
Think Tank Network Analysis

Loads a list of think-tank domains labelled by country and finds all links
between them. Each country group gets its own legend entry in the visualiser.
"""

import csv
import os
import pickle
from typing import TYPE_CHECKING, Optional

from example_loader import (
    get_example_data_path,
    load_domains,
    print_graph_summary,
    require_networkx,
    setup_webgraph,
    validate_domains,
)

if TYPE_CHECKING:
    import networkx as nx


def load_domains_with_country(file_path: str) -> dict:
    """Return {domain: country} from a two-column CSV with headers url,country."""
    mapping = {}
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, skipinitialspace=True):
            url = row["url"].strip()
            country = row["country"].strip()
            if url:
                mapping[url] = country
    return mapping


def build_network(
    file_path: str = None,
    webgraph_dir: Optional[str] = None,
    webgraph_version: Optional[str] = None,
    auto_download: bool = False,
    wg=None,
) -> "nx.DiGraph":
    """
    Build network of links between think-tank domains, grouped by country.

    Args:
        file_path: Path to CSV file (url, country columns). Defaults to example data.
        webgraph_dir: Path to webgraph data files. Falls back to WEBGRAPH_DIR
            env var, then ~/.pyccwebgraph/data.
        webgraph_version: Webgraph version string. Falls back to WEBGRAPH_VERSION
            env var, then "cc-main-2024-feb-apr-may".
        auto_download: If True and data missing, download automatically (~23GB).
        wg: Optional pre-loaded CCWebgraph instance.

    Returns:
        NetworkX DiGraph with:
        - Think-tank domains as nodes, node_type set to their country label
        - Backlink domains as nodes with node_type="backlink"
        - Edges representing links between the domains
    """
    if file_path is None:
        file_path = get_example_data_path("think_tanks.csv")

    domain_country = load_domains_with_country(file_path)
    domains = list(domain_country.keys())
    print(f"Loaded {len(domains)} domains from {file_path}")

    wg = setup_webgraph(webgraph_dir, webgraph_version, auto_download, wg=wg)

    valid_domains, _ = validate_domains(wg, domains)

    edges = wg.get_links_between(
        domains_from=valid_domains,
        domains_to=valid_domains,
    )
    print(f"Found {len(edges)} links between domains")

    backlink_domains, _ = validate_domains(
        wg, load_domains(get_example_data_path("think_tank_backlinkers.csv"))
    )

    backlink_edges = wg.get_links_between(
        domains_from=backlink_domains,
        domains_to=valid_domains,
    )
    print(f"Found {len(backlink_edges)} backlinks to valid domains")

    nx = require_networkx()
    G = nx.DiGraph()

    for domain in valid_domains:
        country = domain_country.get(domain, "unknown")
        G.add_node(domain, is_seed=True, node_type=country)

    for domain in backlink_domains:
        if domain not in G:
            G.add_node(domain, is_seed=False, node_type="backlink")

    G.add_edges_from(edges, edge_type="internal")
    G.add_edges_from(backlink_edges, edge_type="backlink")

    print(f"Final graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


if __name__ == "__main__":
    G = build_network()

    os.makedirs("examples/pickle", exist_ok=True)
    with open("examples/pickle/think_tanks.pkl", "wb") as f:
        pickle.dump(G, f)
    print_graph_summary(G)
