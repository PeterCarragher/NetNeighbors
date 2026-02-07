# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetNeighbors is a domain discovery tool that finds related domains using link topology analysis from the CommonCrawl webgraph (93.9M domains, 1.6B edges). Given seed domains, it discovers other domains connected via backlinks or outlinks. Built for misinformation researchers and fact-checkers at CMU's CASOS Lab.

## Architecture

The system has two layers: a **Java discovery engine** for high-performance graph traversal and a **Python orchestration layer** for UI and data processing.

### Java Core (`src/`)
- `DiscoveryTool.java` — Memory-optimized two-pass discovery algorithm. Pass 1 scans gzipped vertices to map seed names to graph IDs; the graph loads via memory-mapped I/O (not heap); Pass 2 resolves result IDs back to domain names. Uses fastutil primitive collections to minimize GC pressure.
- `GraphLookup.java` — Helper for graph ID/label mapping.
- Compiled class files go to `bin/`.

### Python Frontends
- `app.py` — Gradio web UI (port 7860, configurable via `PORT` env var).
- `graph_bridge.py` — py4j bridge to a persistent JVM. Loads graph once, then queries are near-instant. Used by `app.py`.
- `webgraph_discovery.py` — Subprocess-based alternative that spawns a new Java process per query. No persistent JVM needed.
- `utils.py` — Helpers for setup, webgraph download, and storage management.

### Two Graph Strategy
- Forward graph (`domain-edges.txt.gz`): for outlinks discovery (who do seeds link to).
- Transpose graph (`-t.graph`): for backlinks discovery (who links to seeds).
- Both loaded via memory-mapped I/O, keeping heap usage low.

## Build & Run Commands

### Initial Setup
```bash
./scripts/setup.sh              # Auto-detect environment (Colab or local)
./scripts/setup.sh --local      # Local dev (skips apt-get)
```
This installs Java 17, Maven, Python deps, clones/builds cc-webgraph, and compiles DiscoveryTool.

### Verify Installation
```bash
./scripts/verify.sh
```

### Compile Java (after modifying `src/`)
```bash
javac -cp /path/to/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar -d bin/ src/DiscoveryTool.java
```
The cc-webgraph JAR is at `cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar` (or `$CC_WEBGRAPH_JAR` in Docker).

### Run Gradio App
```bash
python app.py
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
docker run -p 7860:7860 -v /path/to/webgraph:/data/webgraph netneighbors
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
| `PORT` | `7860` | Gradio server port |

## Dependencies

**Java**: JDK 17+, Maven, cc-webgraph (cloned and built from github.com/commoncrawl/cc-webgraph)

**Python** (`requirements.txt`): gradio, py4j, pandas, tqdm, psutil, ipywidgets

**Data**: CommonCrawl webgraph files (~23GB) — downloaded via `utils.download_webgraph()` or gcsfuse mount.

## Memory Requirements

- Local: `-Xmx24g` JVM heap (graph itself uses memory-mapped I/O, not heap)
- Colab: 52GB+ RAM runtime required (`-Xmx48g`)
- Cloud Run: 32Gi memory, 8 CPUs (configured in `cloudbuild.yaml`)
