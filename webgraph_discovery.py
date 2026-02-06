"""
WebgraphDiscovery - Domain discovery using CommonCrawl webgraph.

This module provides a Python wrapper for running domain discovery
using the Java DiscoveryTool.
"""

import subprocess
import pandas as pd
import os
import gzip
import tempfile
from typing import List, Tuple


def _detect_base_dir() -> str:
    """Auto-detect base directory (parent of NetNeighbors, where cc-webgraph lives)."""
    if os.path.exists("/content"):
        return "/content"
    # Running from inside NetNeighbors, base is parent directory
    return os.path.dirname(os.getcwd())


def _detect_netneighbors_dir() -> str:
    """Find NetNeighbors directory (current working directory when running from notebook)."""
    # When notebook sets cwd to NetNeighbors, this is just cwd
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "src", "DiscoveryTool.java")):
        return cwd
    # Fallback to directory containing this file
    return os.path.dirname(os.path.abspath(__file__))


class WebgraphDiscovery:
    """
    Wrapper class for running webgraph discovery using the DiscoveryTool.
    """

    def __init__(self, webgraph_dir: str, version: str, base_dir: str = None):
        self.webgraph_dir = webgraph_dir
        self.version = version

        # Auto-detect base directory if not provided
        if base_dir is None:
            base_dir = _detect_base_dir()
        self.base_dir = base_dir

        # Set paths relative to base directory
        self.jar_path = os.path.join(base_dir, "cc-webgraph", "target",
                                      "cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar")
        self.tool_class_path = os.path.join(_detect_netneighbors_dir(), "bin")
        self.graph_base = os.path.join(webgraph_dir, f"{version}-domain")
        self.vertices_file = os.path.join(webgraph_dir, f"{version}-domain-vertices.txt.gz")

    def validate_seeds(self, seed_domains: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate which seed domains exist in webgraph.

        Memory-efficient: Only scans for the specific seed domains,
        doesn't load all 100M+ domains into memory.
        """
        # Normalize seed domains
        seed_set = {d.strip().lower() for d in seed_domains}
        found = set()

        print(f"Validating {len(seed_set)} seed domains...")

        with gzip.open(self.vertices_file, 'rt', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    reversed_domain = parts[1]
                    # Convert back to normal notation
                    domain = '.'.join(reversed(reversed_domain.split('.')))

                    if domain in seed_set:
                        found.add(domain)
                        if len(found) == len(seed_set):
                            break  # Found all seeds, stop scanning

        not_found = list(seed_set - found)
        print(f"✅ Found {len(found)}/{len(seed_set)} domains in webgraph")

        return list(found), not_found

    def discover(self,
                 seed_domains: List[str],
                 min_connections: int,
                 direction: str = 'backlinks',
                 output_file: str = None) -> pd.DataFrame:
        """
        Run discovery algorithm using the DiscoveryTool.

        Args:
            seed_domains: List of seed domain names
            min_connections: Minimum number of connections to include in results
            direction: 'backlinks' (who links TO seeds) or 'outlinks' (who seeds link TO)
            output_file: Path to save results CSV. If None, uses temp file (Colab uses /content/results.csv)

        Returns:
            DataFrame with columns: domain, connections, percentage
        """
        # Write seeds to temp file
        seeds_fd, seeds_file = tempfile.mkstemp(suffix='.txt', prefix='seeds_')
        try:
            with os.fdopen(seeds_fd, 'w') as f:
                for domain in seed_domains:
                    f.write(domain.strip().lower() + '\n')
        except:
            os.close(seeds_fd)
            raise

        # Determine results file location
        if output_file is not None:
            results_file = output_file
        elif os.path.exists("/content"):
            # Colab: use /content for easy download link
            results_file = '/content/results.csv'
        else:
            # Local: use temp file
            _, results_file = tempfile.mkstemp(suffix='.csv', prefix='results_')

        self._last_results_file = results_file  # Store for later access

        # Build Java command
        # Use moderate heap since graph is memory-mapped (uses OS page cache, not heap)
        cmd = [
            'java',
            '-Xmx24g',  # Reduced heap - graph uses memory-mapped I/O
            '-cp', f'{self.jar_path}:{self.tool_class_path}',
            'DiscoveryTool',
            '--graph', self.graph_base,
            '--vertices', self.vertices_file,
            '--seeds', seeds_file,
            '--output', results_file,
            '--min-connections', str(min_connections),
            '--direction', direction
        ]

        print(f"Running discovery ({direction}, min_connections={min_connections})...")
        print(f"Seed domains: {len(seed_domains)}")
        print()

        try:
            # Run the discovery tool
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            # Print output
            if result.stdout:
                print(result.stdout)

            if result.returncode != 0:
                print("Error output:")
                print(result.stderr)
                raise Exception(f"Discovery failed with return code {result.returncode}")

            # Read results CSV
            if os.path.exists(results_file):
                df = pd.read_csv(results_file)
                return df
            else:
                print("No results file generated")
                return pd.DataFrame(columns=['domain', 'connections', 'percentage'])

        except subprocess.TimeoutExpired:
            raise Exception("Discovery timed out (>10 minutes). Try fewer seed domains.")
        except Exception as e:
            raise Exception(f"Discovery error: {str(e)}")
        finally:
            # Clean up temp seeds file
            if os.path.exists(seeds_file):
                os.remove(seeds_file)
