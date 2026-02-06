"""
WebgraphDiscovery - Domain discovery using CommonCrawl webgraph.

This module provides a Python wrapper for running domain discovery
using the Java DiscoveryTool.
"""

import subprocess
import pandas as pd
import os
import gzip
from typing import List, Tuple


class WebgraphDiscovery:
    """
    Wrapper class for running webgraph discovery using the DiscoveryTool.
    """

    def __init__(self, webgraph_dir: str, version: str):
        self.webgraph_dir = webgraph_dir
        self.version = version
        self.jar_path = "/content/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar"
        self.tool_class_path = "/content/NetNeighbors/bin"
        self.graph_base = os.path.join(webgraph_dir, f"{version}-domain")
        self.vertices_file = os.path.join(webgraph_dir, f"{version}-domain-vertices.txt.gz")

        # Cache for domain validation
        self._domain_set = None

    def _load_domain_set(self) -> set:
        """Load set of all domains in webgraph (for validation)"""
        if self._domain_set is not None:
            return self._domain_set

        print("Loading domain list (one-time, ~30 seconds)...")
        domains = set()
        with gzip.open(self.vertices_file, 'rt', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    reversed_domain = parts[1]
                    # Convert back to normal notation
                    domain = '.'.join(reversed(reversed_domain.split('.')))
                    domains.add(domain)

        self._domain_set = domains
        print(f"✅ Loaded {len(domains):,} domains")
        return domains

    def validate_seeds(self, seed_domains: List[str]) -> Tuple[List[str], List[str]]:
        """Validate which seed domains exist in webgraph"""
        domain_set = self._load_domain_set()

        found = []
        not_found = []

        for domain in seed_domains:
            domain_clean = domain.strip().lower()
            if domain_clean in domain_set:
                found.append(domain_clean)
            else:
                not_found.append(domain_clean)

        return found, not_found

    def discover(self,
                 seed_domains: List[str],
                 min_connections: int,
                 direction: str = 'backlinks') -> pd.DataFrame:
        """
        Run discovery algorithm using the DiscoveryTool.

        Args:
            seed_domains: List of seed domain names
            min_connections: Minimum number of connections to include in results
            direction: 'backlinks' (who links TO seeds) or 'outlinks' (who seeds link TO)

        Returns:
            DataFrame with columns: domain, connections, percentage
        """
        # Write seeds to file
        seeds_file = '/content/seeds.txt'
        with open(seeds_file, 'w') as f:
            for domain in seed_domains:
                f.write(domain.strip().lower() + '\n')

        results_file = '/content/results.csv'

        # Build Java command
        cmd = [
            'java',
            '-Xmx48g',  # Use 48GB heap
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
