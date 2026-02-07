#!/bin/bash
# Build the vertex map for CommonCrawl webgraph exploration.
#
# This wraps cc-webgraph's graph_explore_build_vertex_map.sh which builds
# an ImmutableExternalPrefixMap (iepm) for bidirectional domain↔ID lookups.
#
# Usage:
#   ./scripts/build_vertex_map.sh <webgraph_dir> <version>
#
# Example:
#   ./scripts/build_vertex_map.sh /mnt/d/dev/data/cc cc-main-2024-feb-apr-may
#
# Prerequisites:
#   - cc-webgraph cloned and built (run setup.sh first)
#   - Webgraph files downloaded to <webgraph_dir>

set -e

WEBGRAPH_DIR="$1"
VERSION="$2"

if [ -z "$WEBGRAPH_DIR" ] || [ -z "$VERSION" ]; then
    echo "Usage: $(basename $0) <webgraph_dir> <version>"
    echo
    echo "  <webgraph_dir>  Directory containing webgraph files"
    echo "  <version>       Webgraph version (e.g. cc-main-2024-feb-apr-may)"
    exit 1
fi

GRAPH_NAME="${VERSION}-domain"
VERTICES="${GRAPH_NAME}-vertices.txt.gz"

# Locate cc-webgraph
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETNEIGHBORS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CC_WEBGRAPH_DIR="${CC_WEBGRAPH_DIR:-$(cd "$NETNEIGHBORS_DIR/.." && pwd)/cc-webgraph}"

BUILD_SCRIPT="$CC_WEBGRAPH_DIR/src/script/webgraph_ranking/graph_explore_build_vertex_map.sh"

if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "❌ cc-webgraph not found at: $CC_WEBGRAPH_DIR"
    echo "   Expected script: $BUILD_SCRIPT"
    echo "   Run setup.sh first, or set CC_WEBGRAPH_DIR"
    exit 1
fi

# Verify graph files exist
if [ ! -f "$WEBGRAPH_DIR/$GRAPH_NAME.graph" ]; then
    echo "❌ Graph file not found: $WEBGRAPH_DIR/$GRAPH_NAME.graph"
    echo "   Download webgraph files first"
    exit 1
fi

if [ ! -f "$WEBGRAPH_DIR/$VERTICES" ]; then
    echo "❌ Vertices file not found: $WEBGRAPH_DIR/$VERTICES"
    echo "   Download webgraph files first"
    exit 1
fi

# Check if vertex map already built
if [ -f "$WEBGRAPH_DIR/$GRAPH_NAME.iepm" ]; then
    echo "✅ Vertex map already exists: $GRAPH_NAME.iepm"
    exit 0
fi

# Also check for fallback format (mph + fcl + smph)
if [ -f "$WEBGRAPH_DIR/$GRAPH_NAME.mph" ] && \
   [ -f "$WEBGRAPH_DIR/$GRAPH_NAME.fcl" ] && \
   [ -f "$WEBGRAPH_DIR/$GRAPH_NAME.smph" ]; then
    echo "✅ Vertex map already exists (mph/fcl/smph format)"
    exit 0
fi

echo "Building vertex map for $GRAPH_NAME..."
echo "  Graph directory: $WEBGRAPH_DIR"
echo "  cc-webgraph: $CC_WEBGRAPH_DIR"
echo "  This may take several minutes..."
echo

# The upstream script expects to run from the directory containing graph files
cd "$WEBGRAPH_DIR"
bash "$BUILD_SCRIPT" "$GRAPH_NAME" "$VERTICES"
