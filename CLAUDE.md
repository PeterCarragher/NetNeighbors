# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetNeighbors is a domain discovery tool that finds related domains using link topology analysis from the CommonCrawl webgraph (93.9M domains, 1.6B edges). Given seed domains, it discovers other domains connected via backlinks or outlinks. Built for misinformation researchers and fact-checkers at CMU's CASOS Lab.

## Architecture

The system has two layers: **pyccwebgraph** (a standalone Python package for webgraph access) and a **Dash Cytoscape web UI** for interactive exploration.

### pyccwebgraph (separate project — `pip install pyccwebgraph`)
Standalone Python package providing the `CCWebgraph` class:
- `ccwebgraph.py` — Main API: `CCWebgraph.setup()`, `discover_backlinks/outlinks`, `domain_to_id`, `get_predecessors/successors`. Uses py4j to bridge Python and a persistent JVM. Handles CommonCrawl's reversed domain notation transparently.
- `converters.py` — `DiscoveryResult` class with `.networkx()`, `.networkit()`, `.igraph()`, `.to_dataframe()` converters.
- `setup_utils.py` — Java version checking, JAR auto-detection, data validation.
- `download.py` — Webgraph file download with progress bars, offset building.

### Dash App
- `discovery_network_vis.py` — Interactive graph explorer using Dash Cytoscape. Imports `CCWebgraph` from pyccwebgraph. Port 8050 (configurable via `PORT` env var).

### Java Core (`src/`)
- `DiscoveryTool.java` — Memory-optimized two-pass CLI discovery tool. Not required by the Dash app (which uses py4j bridge instead), but useful for batch processing.
- `GraphLookup.java` — Helper for graph ID/label mapping.

### Two Graph Strategy
- Forward graph (`.graph`): for outlinks discovery (who do seeds link to).
- Transpose graph (`-t.graph`): for backlinks discovery (who links to seeds).
- Both loaded via memory-mapped I/O, keeping heap usage low.

## Build & Run Commands

### Initial Setup
```bash
./scripts/setup.sh              # Auto-detect environment (Colab or local)
./scripts/setup.sh --local      # Local dev (skips apt-get)
```
This installs Java 17, Maven, Python deps, clones/builds cc-webgraph.

### Install pyccwebgraph
```bash
pip install pyccwebgraph
```

### Run Dash App
```bash
python discovery_network_vis.py
```

### Run Java Discovery Directly
```bash
java -Xmx24g -cp cc-webgraph.jar:bin DiscoveryTool \
  --graph /path/graph-base --vertices /path/vertices.txt.gz \
  --seeds seeds.txt --output results.csv \
  --min-connections 5 --direction backlinks
```

### Docker
```bash
docker build -t netneighbors .
docker run -p 8050:8050 -v /path/to/webgraph:/data/webgraph netneighbors
```

### Cloud Run Deployment
```bash
./scripts/deploy.sh   # Uses cloudbuild.yaml, deploys to us-central1
```

## Key Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `WEBGRAPH_DIR` | `/data/webgraph` | Path to webgraph data directory |
| `WEBGRAPH_VERSION` | `cc-main-2024-feb-apr-may` | CommonCrawl crawl version identifier |
| `CC_WEBGRAPH_JAR` | (set by setup) | Path to cc-webgraph uber-jar |
| `PORT` | `8050` | Dash server port |

## Dependencies

**Java**: JDK 17+, Maven, cc-webgraph (cloned and built from github.com/commoncrawl/cc-webgraph)

**Python** (`requirements.txt`): dash, dash-cytoscape, pyccwebgraph (py4j, tqdm, psutil), pandas

**Data**: CommonCrawl webgraph files (~23GB) — downloaded via `pyccwebgraph.download.download_webgraph()` or `CCWebgraph.setup(auto_download=True)`.

## Memory Requirements

- Local: `-Xmx24g` JVM heap (graph itself uses memory-mapped I/O, not heap)
- Colab: 52GB+ RAM runtime required (`-Xmx48g`)
- Cloud Run: 32Gi memory, 8 CPUs (configured in `cloudbuild.yaml`)
