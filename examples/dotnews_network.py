"""
Dotnews Network

Extends the news credibility network with two additional node groups:
domains that link TO .news domains (backlink .news) and domains that
.news domains link TO (outlink .news), discovered via the CommonCrawl
webgraph. Loaded directly from a pre-built GEXF file.
"""

import os
import pickle
from pathlib import Path

import networkx as nx


GEXF_PATH = Path(__file__).parent / "example_data" / "dotnews_network.gexf"


def build_network(file_path: str = None) -> nx.DiGraph:
    """
    Build the dotnews network from the pre-computed GEXF file.

    Node attribute `node_type` is set from the GEXF `hop_label` field so
    the webapp legend shows the correct group names.  Nodes are inserted in
    ascending hop order so the type → hop mapping in the loader is stable.

    Returns:
        NetworkX DiGraph with node attributes: node_type, connections.
    """
    if file_path is None:
        file_path = str(GEXF_PATH)

    G_raw = nx.read_gexf(file_path)

    # Sort by stored hop so type_to_hop ordering is deterministic (mixed=0,
    # unknown=1, reliable=2, unreliable=3, backlink .news=4, outlink .news=5).
    sorted_nodes = sorted(
        G_raw.nodes(data=True),
        key=lambda x: int(x[1].get('hop', 0))
    )

    G = nx.DiGraph()
    for node_id, data in sorted_nodes:
        G.add_node(
            node_id,
            node_type=data.get('hop_label', '').strip(),
            connections=int(data.get('connections', 0)),
        )

    for src, tgt in G_raw.edges():
        if G.has_node(src) and G.has_node(tgt):
            G.add_edge(src, tgt)

    return G


if __name__ == "__main__":
    G = build_network()

    os.makedirs("examples/pickle", exist_ok=True)
    with open("examples/pickle/dotnews_network.pkl", "wb") as f:
        pickle.dump(G, f)

    from collections import Counter
    type_counts = Counter(d.get('node_type', '') for _, d in G.nodes(data=True))
    print(f"Saved dotnews_network.pkl: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    for label, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {label}: {count}")
