"""
Iranian News Network Analysis

Loads Iranian news domains, finds internal links between them,
discovers external sites that backlink to at least 10 of these domains,
and returns a combined network graph.
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
    min_connections: int = 10,
    webgraph_dir: Optional[str] = None,
    webgraph_version: Optional[str] = None,
    auto_download: bool = False,
    wg=None,
) -> "nx.DiGraph":
    """
    Build Iranian news network graph.

    Args:
        file_path: Path to domain list file. Defaults to example data.
        min_connections: Minimum backlink connections for discovered sites.
        webgraph_dir: Path to webgraph data files. Falls back to WEBGRAPH_DIR
            env var, then ~/.pyccwebgraph/data.
        webgraph_version: Webgraph version string. Falls back to WEBGRAPH_VERSION
            env var, then "cc-main-2024-feb-apr-may".
        auto_download: If True and data missing, download automatically (~23GB).
        wg: Optional pre-loaded CCWebgraph instance.

    Returns:
        NetworkX DiGraph with:
        - Seed nodes (Iranian news domains) with is_seed=True
        - Discovered nodes (backlinking sites) with connections count
        - Internal edges between seed domains
        - External edges from discovered sites to seeds
    """
    if file_path is None:
        file_path = get_example_data_path("iranian_news_domains.csv")

    # Load domains
    domains = load_domains(file_path)
    print(f"Loaded {len(domains)} domains from {file_path}")

    # Initialize webgraph (or use provided instance)
    wg = setup_webgraph(webgraph_dir, webgraph_version, auto_download, wg=wg)

    # Validate domains
    valid_domains, _ = validate_domains(wg, domains)

    # Get internal links between the seed domains
    internal_edges = wg.get_links_between(
        domains_from=valid_domains,
        domains_to=valid_domains,
    )
    print(f"Found {len(internal_edges)} internal links between seed domains")

    # Discover external sites that backlink to these domains
    discovery = wg.discover_backlinks(
        seeds=valid_domains,
        min_connections=min_connections,
    )
    print(f"Found {len(discovery.nodes)} external sites with >= {min_connections} backlinks")

    # Build NetworkX graph
    nx = require_networkx()
    G = nx.DiGraph()

    # Add seed nodes
    for domain in valid_domains:
        G.add_node(domain, is_seed=True, node_type="seed")

    # Add internal edges
    G.add_edges_from(internal_edges, edge_type="internal")

    # Add discovered nodes and their edges
    for node in discovery.nodes:
        G.add_node(
            node["domain"],
            is_seed=False,
            node_type="discovered",
            connections=node["connections"],
            percentage=node["percentage"],
        )

    for src, tgt in discovery.edges:
        G.add_edge(src, tgt, edge_type="external")

    print(f"Final graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


if __name__ == "__main__":
    G = build_network()
    os.makedirs("examples/pickle", exist_ok=True)
    with open("examples/pickle/iranian_news_network.pkl", "wb") as f:
        pickle.dump(G, f)
    print_graph_summary(G)
