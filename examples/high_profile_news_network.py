"""
High-Profile News Network Analysis

Loads a list of high-profile news domains and finds all links
between them. Unlike other examples, this does not discover
external sites - it only maps connections within the given set.
"""

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


def build_network(
    file_path: str = None,
    webgraph_dir: Optional[str] = None,
    webgraph_version: Optional[str] = None,
    auto_download: bool = False,
    wg=None,
) -> "nx.DiGraph":
    """
    Build network of links between high-profile news domains.

    Args:
        file_path: Path to domain list file. Defaults to example data.
        webgraph_dir: Path to webgraph data files. Falls back to WEBGRAPH_DIR
            env var, then ~/.pyccwebgraph/data.
        webgraph_version: Webgraph version string. Falls back to WEBGRAPH_VERSION
            env var, then "cc-main-2024-feb-apr-may".
        auto_download: If True and data missing, download automatically (~23GB).
        wg: Optional pre-loaded CCWebgraph instance.

    Returns:
        NetworkX DiGraph with:
        - All input domains as nodes (is_seed=True)
        - Edges representing links between the domains
    """
    if file_path is None:
        file_path = get_example_data_path("high_profile_news_domains.csv")

    # Load domains
    domains = load_domains(file_path)
    print(f"Loaded {len(domains)} domains from {file_path}")

    # Initialize webgraph (or use provided instance)
    wg = setup_webgraph(webgraph_dir, webgraph_version, auto_download, wg=wg)

    # Validate domains
    valid_domains, _ = validate_domains(wg, domains)

    # Get all links between these domains
    edges = wg.get_links_between(
        domains_from=valid_domains,
        domains_to=valid_domains,
    )
    print(f"Found {len(edges)} links between domains")

    # Build NetworkX graph
    nx = require_networkx()
    G = nx.DiGraph()

    # Add all valid domains as seed nodes
    for domain in valid_domains:
        G.add_node(domain, is_seed=True, node_type="seed")

    # Add edges
    G.add_edges_from(edges, edge_type="internal")

    print(f"Final graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


if __name__ == "__main__":
    G = build_network()
    # dump to pickle file
    
    os.makedirs("examples/pickle", exist_ok=True)
    with open("examples/pickle/high_profile_news_network.pkl", "wb") as f:
        pickle.dump(G, f)
    print_graph_summary(G)
