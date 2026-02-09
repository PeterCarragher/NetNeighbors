"""
Shared utilities for example network scripts.

Provides common functions for loading domains, initializing the webgraph,
and building NetworkX graphs.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    import networkx as nx
    from pyccwebgraph import CCWebgraph


def load_domains(file_path: str) -> List[str]:
    """
    Load domain names from a file (one per line).

    Args:
        file_path: Path to file containing domain names.

    Returns:
        List of domain name strings.
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        domains = [line.strip() for line in f if line.strip()]
    return domains


def get_example_data_path(filename: str) -> Path:
    """Get path to a file in the example_data directory."""
    return Path(__file__).parent / "example_data" / filename


def setup_webgraph(
    webgraph_dir: Optional[str] = None,
    webgraph_version: Optional[str] = None,
    auto_download: bool = False,
    wg: Optional["CCWebgraph"] = None,
) -> "CCWebgraph":
    """
    Initialize CCWebgraph with environment variable fallbacks.

    Args:
        webgraph_dir: Path to webgraph data files. Falls back to WEBGRAPH_DIR
            env var, then ~/.pyccwebgraph/data.
        webgraph_version: Webgraph version string. Falls back to WEBGRAPH_VERSION
            env var, then "cc-main-2024-feb-apr-may".
        auto_download: If True and data missing, download automatically (~23GB).
        wg: Optional pre-loaded CCWebgraph instance. If provided, returns it
            directly without loading a new one.

    Returns:
        Initialized CCWebgraph instance with loaded graph.
    """
    # If a webgraph instance is provided, use it directly
    if wg is not None:
        return wg

    from pyccwebgraph import CCWebgraph

    # Resolve from env vars if not provided
    if webgraph_dir is None:
        webgraph_dir = os.environ.get("WEBGRAPH_DIR")
    if webgraph_version is None:
        webgraph_version = os.environ.get("WEBGRAPH_VERSION")

    # Build kwargs, only including non-None values
    setup_kwargs = {"auto_download": auto_download}
    if webgraph_dir is not None:
        setup_kwargs["webgraph_dir"] = webgraph_dir
    if webgraph_version is not None:
        setup_kwargs["version"] = webgraph_version

    return CCWebgraph.setup(**setup_kwargs)


def validate_domains(
    wg: "CCWebgraph",
    domains: List[str],
    verbose: bool = True,
) -> Tuple[List[str], List[str]]:
    """
    Validate which domains exist in the webgraph.

    Args:
        wg: Initialized CCWebgraph instance.
        domains: List of domain names to validate.
        verbose: If True, print validation summary.

    Returns:
        Tuple of (valid_domains, missing_domains).
    """
    valid_domains, missing = wg.validate_seeds(domains)
    if verbose:
        if missing:
            print(f"Note: {len(missing)} domains not found in webgraph")
        print(f"Using {len(valid_domains)} valid domains")
    return valid_domains, missing


def require_networkx():
    """Import and return networkx, raising helpful error if missing."""
    try:
        import networkx as nx
        return nx
    except ImportError:
        raise ImportError(
            "NetworkX required. Install with: pip install networkx"
        )


def print_graph_summary(G: "nx.DiGraph") -> None:
    """Print summary statistics for a network graph."""
    seed_count = sum(1 for _, d in G.nodes(data=True) if d.get("is_seed"))
    discovered_count = sum(1 for _, d in G.nodes(data=True) if not d.get("is_seed"))
    internal_edges = sum(
        1 for _, _, d in G.edges(data=True) if d.get("edge_type") == "internal"
    )
    external_edges = sum(
        1 for _, _, d in G.edges(data=True) if d.get("edge_type") == "external"
    )

    print(f"\nGraph summary:")
    print(f"  Seed domains: {seed_count}")
    if discovered_count > 0:
        print(f"  Discovered sites: {discovered_count}")
    print(f"  Internal edges: {internal_edges}")
    if external_edges > 0:
        print(f"  External edges: {external_edges}")
