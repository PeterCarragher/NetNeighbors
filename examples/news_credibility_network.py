"""
News Credibility Network Analysis

Loads a credibility-labeled list of news domains and maps all links
between them. Each node's type reflects its credibility label
(reliable, unreliable, or mixed).
"""

import os
import pickle
from typing import TYPE_CHECKING, Optional

import pandas as pd

from example_loader import (
    get_example_data_path,
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
    Build network of links between credibility-labeled news domains.

    Args:
        file_path: Path to CSV file with 'url' and 'label' columns.
            Defaults to example data (news_credibility.csv).
        webgraph_dir: Path to webgraph data files. Falls back to WEBGRAPH_DIR
            env var, then ~/.pyccwebgraph/data.
        webgraph_version: Webgraph version string. Falls back to WEBGRAPH_VERSION
            env var, then "cc-main-2024-feb-apr-may".
        auto_download: If True and data missing, download automatically (~23GB).
        wg: Optional pre-loaded CCWebgraph instance.

    Returns:
        NetworkX DiGraph with:
        - All input domains as nodes (is_seed=True, node_type=label)
        - Edges representing links between the domains
    """
    if file_path is None:
        file_path = get_example_data_path("news_credibility.csv")

    df = pd.read_csv(file_path, encoding="utf-8-sig").dropna(subset=["url", "label"])
    df["url"] = df["url"].str.strip()
    df["label"] = df["label"].str.strip()
    df = pd.concat([
        group.sample(min(100, len(group)), random_state=42)
        for _, group in df.groupby("label")
    ])
    domain_to_label = dict(zip(df["url"], df["label"]))
    domains = list(domain_to_label.keys())
    print(f"Loaded {len(domains)} domains from {file_path} (100 per label)")

    wg = setup_webgraph(webgraph_dir, webgraph_version, auto_download, wg=wg)

    valid_domains, _ = validate_domains(wg, domains)

    edges = wg.get_links_between(
        domains_from=valid_domains,
        domains_to=valid_domains,
    )
    print(f"Found {len(edges)} links between domains")

    nx = require_networkx()
    G = nx.DiGraph()

    for domain in valid_domains:
        G.add_node(domain, is_seed=True, node_type=domain_to_label.get(domain, "unknown"))

    G.add_edges_from(edges, edge_type="internal")

    print(f"Final graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


if __name__ == "__main__":
    G = build_network()

    os.makedirs("examples/pickle", exist_ok=True)
    with open("examples/pickle/news_credibility_network.pkl", "wb") as f:
        pickle.dump(G, f)
    print_graph_summary(G)
