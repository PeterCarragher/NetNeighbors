"""
GraphBridge - High-performance Python interface to CommonCrawl webgraph via py4j.

Uses py4j to maintain a persistent JVM with the graph loaded in memory.
After initial load (~5 seconds), queries are nearly instant.
"""

import os
import atexit
from typing import List, Dict, Optional, Tuple

try:
    from py4j.java_gateway import JavaGateway, GatewayParameters, launch_gateway
    HAS_PY4J = True
except ImportError:
    HAS_PY4J = False


def _detect_paths() -> Tuple[str, str]:
    """Auto-detect cc-webgraph JAR and base directory."""
    if os.path.exists("/content"):
        base_dir = "/content"
    else:
        # Running from inside NetNeighbors, base is parent directory
        base_dir = os.path.dirname(os.getcwd())

    jar_path = os.path.join(
        base_dir, "cc-webgraph", "target",
        "cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar"
    )
    return base_dir, jar_path


class GraphBridge:
    """
    High-performance bridge to CommonCrawl webgraph using py4j.

    The graph is loaded once and kept in JVM memory. Subsequent queries
    are nearly instant compared to spawning new Java processes.

    Usage:
        bridge = GraphBridge(webgraph_dir, version)
        bridge.load_graph()  # Takes ~5 seconds, then graph stays loaded

        # Instant queries after loading
        results = bridge.discover_backlinks(["cnn.com", "bbc.com"], min_connections=2)
    """

    def __init__(self, webgraph_dir: str, version: str, jar_path: str = None):
        """
        Initialize the bridge.

        Args:
            webgraph_dir: Directory containing webgraph files
            version: Webgraph version string (e.g., "cc-main-2024-feb-apr-may")
            jar_path: Path to cc-webgraph JAR. If None, auto-detects.
        """
        if not HAS_PY4J:
            raise ImportError(
                "py4j is required for GraphBridge. Install with: pip install py4j"
            )

        self.webgraph_dir = webgraph_dir
        self.version = version
        self.graph_base = os.path.join(webgraph_dir, f"{version}-domain")

        if jar_path is None:
            _, jar_path = _detect_paths()
        self.jar_path = jar_path

        self.gateway = None
        self.graph = None
        self._port = None

    def load_graph(self) -> None:
        """
        Start JVM and load the graph. This takes ~5 seconds but only needs
        to be done once. After loading, all queries are nearly instant.
        """
        if not os.path.exists(self.jar_path):
            raise FileNotFoundError(
                f"cc-webgraph JAR not found at {self.jar_path}\n"
                "Please run setup.sh first."
            )

        print(f"Starting JVM with cc-webgraph...")
        print(f"JAR: {self.jar_path}")

        # Launch JVM with cc-webgraph on classpath
        self._port = launch_gateway(
            classpath=self.jar_path,
            die_on_exit=True,
            redirect_stdout=None,
            redirect_stderr=None
        )

        self.gateway = JavaGateway(
            gateway_parameters=GatewayParameters(port=self._port)
        )

        # Register cleanup on exit
        atexit.register(self.shutdown)

        print(f"Loading graph: {self.graph_base}")
        print("This takes ~5 seconds...")

        # Load the graph using cc-webgraph's Graph class
        Graph = self.gateway.jvm.org.commoncrawl.webgraph.explore.Graph
        self.graph = Graph(self.graph_base)

        print(f"✅ Graph loaded!")
        print("Subsequent queries will be nearly instant!")

    def shutdown(self) -> None:
        """Shutdown the JVM connection."""
        if self.gateway is not None:
            try:
                self.gateway.shutdown()
            except:
                pass
            self.gateway = None
            self.graph = None

    def _ensure_loaded(self) -> None:
        """Ensure graph is loaded."""
        if self.graph is None:
            raise RuntimeError("Graph not loaded. Call load_graph() first.")

    def _java_int_array_to_list(self, java_array) -> List[int]:
        """
        Convert Java int[] to Python list with a single IPC call.

        Instead of N separate array[i] accesses (N IPC calls),
        this converts to string in Java and parses in Python (1 IPC call).
        """
        s = str(self.gateway.jvm.java.util.Arrays.toString(java_array))
        if s == "[]":
            return []
        return [int(x) for x in s[1:-1].split(", ")]

    def _java_long_array_to_list(self, java_array) -> List[int]:
        """Convert Java long[] to Python list with a single IPC call."""
        s = str(self.gateway.jvm.java.util.Arrays.toString(java_array))
        if s == "[]":
            return []
        return [int(x) for x in s[1:-1].split(", ")]

    def domain_to_id(self, domain: str) -> Optional[int]:
        """Convert a domain name to its graph ID."""
        self._ensure_loaded()
        id = self.graph.vertexLabelToId(domain.lower())
        return id if id >= 0 else None

    def id_to_domain(self, id: int) -> Optional[str]:
        """Convert a graph ID to its domain name."""
        self._ensure_loaded()
        return self.graph.vertexIdToLabel(id)

    def domains_to_ids(self, domains: List[str]) -> List[int]:
        """Convert domain names to graph IDs, filtering out not-found domains."""
        self._ensure_loaded()
        ids = []
        for domain in domains:
            id = self.graph.vertexLabelToId(domain.lower())
            if id >= 0:
                ids.append(id)
        return ids

    def ids_to_domains(self, ids: List[int]) -> List[str]:
        """Convert graph IDs to domain names."""
        self._ensure_loaded()
        domains = []
        for id in ids:
            label = self.graph.vertexIdToLabel(id)
            if label is not None:
                domains.append(label)
        return domains

    def validate_seeds(self, seed_domains: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate which seed domains exist in the graph.

        Returns:
            Tuple of (found_domains, not_found_domains)
        """
        self._ensure_loaded()
        found = []
        not_found = []

        for domain in seed_domains:
            domain_clean = domain.strip().lower()
            id = self.graph.vertexLabelToId(domain_clean)
            if id >= 0:
                found.append(domain_clean)
            else:
                not_found.append(domain_clean)

        return found, not_found

    def get_predecessors(self, domain: str) -> List[str]:
        """Get all domains that link TO this domain (backlinks)."""
        self._ensure_loaded()
        id = self.graph.vertexLabelToId(domain.lower())
        if id < 0:
            return []

        # predecessors() returns int[] in Java
        pred_ids = self.graph.predecessors(id)
        results = []
        for i in range(len(pred_ids)):
            label = self.graph.vertexIdToLabel(int(pred_ids[i]))
            if label is not None:
                results.append(label)
        return results

    def get_successors(self, domain: str) -> List[str]:
        """Get all domains that this domain links TO (outlinks)."""
        self._ensure_loaded()
        id = self.graph.vertexLabelToId(domain.lower())
        if id < 0:
            return []

        # successors() returns int[] in Java
        succ_ids = self.graph.successors(id)
        results = []
        for i in range(len(succ_ids)):
            label = self.graph.vertexIdToLabel(int(succ_ids[i]))
            if label is not None:
                results.append(label)
        return results

    def shared_predecessors(self, domains: List[str], min_shared: int = None) -> List[str]:
        """
        Get domains that link to the given domains.
        Uses the optimized cc-webgraph sharedPredecessors method.

        Args:
            domains: List of domain names
            min_shared: Minimum number of domains that must share the predecessor.
                       If None, defaults to len(domains) (intersection).
        """
        self._ensure_loaded()

        # Convert to Java long array
        ids = self.domains_to_ids(domains)
        if not ids:
            return []

        java_ids = self.gateway.new_array(self.gateway.jvm.long, len(ids))
        for i, id in enumerate(ids):
            java_ids[i] = id

        if min_shared is None:
            min_shared = len(ids)

        # sharedPredecessors(vertices, minShared, maxShared)
        result_ids = self.graph.sharedPredecessors(java_ids, min_shared, len(ids))

        # Bulk transfer result array and convert to domains
        id_list = self._java_long_array_to_list(result_ids)
        results = []
        for id in id_list:
            label = self.graph.vertexIdToLabel(id)
            if label is not None:
                results.append(label)
        return results

    def shared_successors(self, domains: List[str], min_shared: int = None) -> List[str]:
        """
        Get domains that the given domains link to.
        Uses the optimized cc-webgraph sharedSuccessors method.

        Args:
            domains: List of domain names
            min_shared: Minimum number of domains that must share the successor.
                       If None, defaults to len(domains) (intersection).
        """
        self._ensure_loaded()

        ids = self.domains_to_ids(domains)
        if not ids:
            return []

        java_ids = self.gateway.new_array(self.gateway.jvm.long, len(ids))
        for i, id in enumerate(ids):
            java_ids[i] = id

        if min_shared is None:
            min_shared = len(ids)

        # sharedSuccessors(vertices, minShared, maxShared)
        result_ids = self.graph.sharedSuccessors(java_ids, min_shared, len(ids))

        # Bulk transfer result array and convert to domains
        id_list = self._java_long_array_to_list(result_ids)
        results = []
        for id in id_list:
            label = self.graph.vertexIdToLabel(id)
            if label is not None:
                results.append(label)
        return results

    def discover(
        self,
        seed_domains: List[str],
        min_connections: int = 1,
        direction: str = "backlinks"
    ) -> List[Dict]:
        """
        Discover domains connected to seed domains.

        This is the main discovery method. For each seed, it finds neighbors
        and counts how many seeds each neighbor is connected to.

        Args:
            seed_domains: List of seed domain names
            min_connections: Minimum number of seed connections required
            direction: "backlinks" (who links TO seeds) or "outlinks" (who seeds link TO)

        Returns:
            List of dicts with keys: domain, connections, percentage
            Sorted by connections descending.
        """
        self._ensure_loaded()

        # Validate seeds
        valid_seeds = []
        seed_ids = []
        for domain in seed_domains:
            domain_clean = domain.strip().lower()
            id = self.graph.vertexLabelToId(domain_clean)
            if id >= 0:
                valid_seeds.append(domain_clean)
                seed_ids.append(int(id))

        if not seed_ids:
            print("No valid seed domains found in graph")
            return []

        print(f"Processing {len(seed_ids)} seed domains...")
        seed_id_set = set(seed_ids)

        # Count connections for each neighbor
        # Uses bulk array transfer to minimize IPC calls
        neighbor_counts = {}

        for i, seed_id in enumerate(seed_ids):
            # Get neighbors based on direction (returns int[] in Java)
            if direction == "backlinks":
                java_neighbors = self.graph.predecessors(seed_id)
            else:
                java_neighbors = self.graph.successors(seed_id)

            # Bulk transfer: convert entire array to Python list in 1 IPC call
            # instead of N separate array[j] accesses
            neighbors = self._java_int_array_to_list(java_neighbors)

            for neighbor_id in neighbors:
                if neighbor_id not in seed_id_set:
                    neighbor_counts[neighbor_id] = neighbor_counts.get(neighbor_id, 0) + 1

            if (i + 1) % 100 == 0 or i == len(seed_ids) - 1:
                print(f"\rProcessed {i + 1}/{len(seed_ids)} seeds...", end="")

        print()
        print(f"Found {len(neighbor_counts):,} unique neighbor domains")

        # Filter by min_connections and build results
        results = []
        for neighbor_id, count in neighbor_counts.items():
            if count >= min_connections:
                domain = self.graph.vertexIdToLabel(neighbor_id)
                if domain:
                    results.append({
                        "domain": domain,
                        "connections": count,
                        "percentage": round(count * 100.0 / len(seed_ids), 2)
                    })

        # Sort by connections descending
        results.sort(key=lambda x: x["connections"], reverse=True)

        print(f"Found {len(results):,} domains with >= {min_connections} connections")
        return results

    def discover_fast(
        self,
        seed_domains: List[str],
        min_connections: int = 1,
        direction: str = "backlinks"
    ) -> List[str]:
        """
        Fast discovery using Java-side filtering (sharedPredecessors/sharedSuccessors).

        This is much faster than discover() because all filtering happens in Java.
        However, it only returns domain names without connection counts.

        Args:
            seed_domains: List of seed domain names
            min_connections: Minimum number of seed connections required
            direction: "backlinks" or "outlinks"

        Returns:
            List of domain names (no counts)
        """
        self._ensure_loaded()

        # Validate seeds and convert to IDs
        valid_seeds = []
        for domain in seed_domains:
            domain_clean = domain.strip().lower()
            id = self.graph.vertexLabelToId(domain_clean)
            if id >= 0:
                valid_seeds.append(domain_clean)

        if not valid_seeds:
            print("No valid seed domains found in graph")
            return []

        print(f"Processing {len(valid_seeds)} seed domains with Java-side filtering...")

        if direction == "backlinks":
            results = self.shared_predecessors(valid_seeds, min_shared=min_connections)
        else:
            results = self.shared_successors(valid_seeds, min_shared=min_connections)

        # Filter out seeds from results
        seed_set = set(valid_seeds)
        results = [d for d in results if d not in seed_set]

        print(f"Found {len(results):,} domains with >= {min_connections} connections")
        return results

    def discover_backlinks(
        self,
        seed_domains: List[str],
        min_connections: int = 1
    ) -> List[Dict]:
        """Convenience method for backlink discovery."""
        return self.discover(seed_domains, min_connections, direction="backlinks")

    def discover_outlinks(
        self,
        seed_domains: List[str],
        min_connections: int = 1
    ) -> List[Dict]:
        """Convenience method for outlink discovery."""
        return self.discover(seed_domains, min_connections, direction="outlinks")
