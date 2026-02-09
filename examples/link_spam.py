"""
Link Spam Network Analysis

Discovers sites that backlink to both scam casinos AND misinformation
domains. These "link spam" sites are likely part of coordinated link
building operations that serve multiple types of problematic content.

Algorithm:
1. Find sites that backlink to >= N scam casino domains
2. Find sites that backlink to >= N misinformation domains
3. Take the intersection of these two sets
4. Return a graph with casinos, misinfo sites, and shared backlinkers
"""

import os
import pickle
from typing import TYPE_CHECKING, Optional, Set

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
    casino_file: str = None,
    misinfo_file: str = None,
    min_connections: int = 10,
    webgraph_dir: Optional[str] = None,
    webgraph_version: Optional[str] = None,
    auto_download: bool = False,
    wg=None,
) -> "nx.DiGraph":
    """
    Build network of sites that backlink to both casinos and misinformation.

    Args:
        casino_file: Path to casino domain list. Defaults to example data.
        misinfo_file: Path to misinformation domain list. Defaults to example data.
        min_connections: Minimum backlinks required for each category.
        webgraph_dir: Path to webgraph data files. Falls back to WEBGRAPH_DIR
            env var, then ~/.pyccwebgraph/data.
        webgraph_version: Webgraph version string. Falls back to WEBGRAPH_VERSION
            env var, then "cc-main-2024-feb-apr-may".
        auto_download: If True and data missing, download automatically (~23GB).
        wg: Optional pre-loaded CCWebgraph instance.

    Returns:
        NetworkX DiGraph with:
        - Casino seed nodes (node_type="casino")
        - Misinformation seed nodes (node_type="misinfo")
        - Shared backlinker nodes (node_type="link_spam")
        - Edges from backlinkers to the seeds they link to
    """
    if casino_file is None:
        casino_file = get_example_data_path("bad_casinos.csv")
    if misinfo_file is None:
        misinfo_file = get_example_data_path("misinformation_domains.csv")

    # Load domain lists
    casino_domains = load_domains(casino_file)
    misinfo_domains = load_domains(misinfo_file)
    print(f"Loaded {len(casino_domains)} casino domains from {casino_file}")
    print(f"Loaded {len(misinfo_domains)} misinformation domains from {misinfo_file}")

    # Initialize webgraph (or use provided instance)
    wg = setup_webgraph(webgraph_dir, webgraph_version, auto_download, wg=wg)

    # Validate domains
    print("\nValidating casino domains...")
    valid_casinos, missing_casinos = validate_domains(wg, casino_domains)

    print("\nValidating misinformation domains...")
    valid_misinfo, missing_misinfo = validate_domains(wg, misinfo_domains)

    # Discover backlinkers for each category
    print(f"\nDiscovering backlinkers to casino domains (min_connections={min_connections})...")
    casino_discovery = wg.discover_backlinks(
        seeds=valid_casinos,
        min_connections=min_connections,
    )
    casino_backlinkers: Set[str] = {node["domain"] for node in casino_discovery.nodes}
    print(f"Found {len(casino_backlinkers)} sites backlinking to >= {min_connections} casinos")

    print(f"\nDiscovering backlinkers to misinformation domains (min_connections={min_connections})...")
    misinfo_discovery = wg.discover_backlinks(
        seeds=valid_misinfo,
        min_connections=min_connections,
    )
    misinfo_backlinkers: Set[str] = {node["domain"] for node in misinfo_discovery.nodes}
    print(f"Found {len(misinfo_backlinkers)} sites backlinking to >= {min_connections} misinfo sites")

    # Find intersection - sites that backlink to BOTH categories
    shared_backlinkers = casino_backlinkers & misinfo_backlinkers
    print(f"\nIntersection: {len(shared_backlinkers)} sites backlink to both categories")

    # Build edge maps for shared backlinkers
    # We need to know which seeds each shared backlinker connects to
    casino_edges = {}  # backlinker -> list of casino targets
    for src, tgt in casino_discovery.edges:
        if src in shared_backlinkers:
            if src not in casino_edges:
                casino_edges[src] = []
            casino_edges[src].append(tgt)

    misinfo_edges = {}  # backlinker -> list of misinfo targets
    for src, tgt in misinfo_discovery.edges:
        if src in shared_backlinkers:
            if src not in misinfo_edges:
                misinfo_edges[src] = []
            misinfo_edges[src].append(tgt)

    # Build NetworkX graph
    nx = require_networkx()
    G = nx.DiGraph()

    # Track which seeds are actually linked by shared backlinkers
    linked_casinos = set()
    linked_misinfo = set()

    for backlinker in shared_backlinkers:
        for casino in casino_edges.get(backlinker, []):
            linked_casinos.add(casino)
        for misinfo in misinfo_edges.get(backlinker, []):
            linked_misinfo.add(misinfo)

    # Add casino seed nodes (only those linked by shared backlinkers)
    for domain in linked_casinos:
        G.add_node(domain, is_seed=True, node_type="casino")

    # Add misinformation seed nodes (only those linked by shared backlinkers)
    for domain in linked_misinfo:
        G.add_node(domain, is_seed=True, node_type="misinfo")

    # Add shared backlinker nodes
    for backlinker in shared_backlinkers:
        casino_count = len(casino_edges.get(backlinker, []))
        misinfo_count = len(misinfo_edges.get(backlinker, []))
        G.add_node(
            backlinker,
            is_seed=False,
            node_type="link_spam",
            casino_connections=casino_count,
            misinfo_connections=misinfo_count,
            total_connections=casino_count + misinfo_count,
        )

    # Add edges from backlinkers to casinos
    for backlinker, casinos in casino_edges.items():
        for casino in casinos:
            G.add_edge(backlinker, casino, edge_type="external", target_type="casino")

    # Add edges from backlinkers to misinformation sites
    for backlinker, misinfos in misinfo_edges.items():
        for misinfo in misinfos:
            G.add_edge(backlinker, misinfo, edge_type="external", target_type="misinfo")

    print(f"\nFinal graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"  - {len(linked_casinos)} casino domains")
    print(f"  - {len(linked_misinfo)} misinformation domains")
    print(f"  - {len(shared_backlinkers)} link spam sites")

    return G


if __name__ == "__main__":
    G = build_network()
    os.makedirs("examples/pickle", exist_ok=True)
    with open("examples/pickle/link_spam.pkl", "wb") as f:
        pickle.dump(G, f)
    print_graph_summary(G)

    # Additional stats for this specific analysis
    link_spam_nodes = [
        (n, d) for n, d in G.nodes(data=True) if d.get("node_type") == "link_spam"
    ]
    if link_spam_nodes:
        print("\nTop 10 link spam sites by total connections:")
        sorted_nodes = sorted(
            link_spam_nodes, key=lambda x: x[1].get("total_connections", 0), reverse=True
        )
        for domain, data in sorted_nodes[:10]:
            print(
                f"  {domain}: {data['casino_connections']} casinos, "
                f"{data['misinfo_connections']} misinfo"
            )
