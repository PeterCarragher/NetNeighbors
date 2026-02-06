#!/bin/bash
# Verification script for NetNeighbors installation
# Checks all required components are present

WEBGRAPH_DIR="${1:-/content/webgraph}"
VERSION="${2:-cc-main-2025-26-nov-dec-jan}"

echo "============================================================"
echo "           INSTALLATION VERIFICATION"
echo "============================================================"
echo ""

ALL_PASSED=true

# Check Java
echo "1. Java Runtime:"
if java -version > /dev/null 2>&1; then
    VERSION_LINE=$(java -version 2>&1 | head -1)
    echo "   ✅ $VERSION_LINE"
else
    echo "   ❌ Java not found"
    ALL_PASSED=false
fi

# Check cc-webgraph JAR
echo ""
echo "2. cc-webgraph Tools:"
JAR_PATH="/content/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar"
if [ -f "$JAR_PATH" ]; then
    SIZE_MB=$(du -m "$JAR_PATH" | cut -f1)
    echo "   ✅ JAR file found (${SIZE_MB} MB)"
else
    echo "   ❌ JAR file not found"
    ALL_PASSED=false
fi

# Check DiscoveryTool
echo ""
echo "3. DiscoveryTool:"
TOOL_PATH="/content/NetNeighbors/bin/DiscoveryTool.class"
if [ -f "$TOOL_PATH" ]; then
    echo "   ✅ DiscoveryTool compiled"
else
    echo "   ❌ DiscoveryTool not found"
    ALL_PASSED=false
fi

# Check webgraph data files
echo ""
echo "4. Webgraph Data Files:"

check_file() {
    local filename=$1
    local description=$2
    local filepath="${WEBGRAPH_DIR}/${filename}"

    if [ -f "$filepath" ]; then
        SIZE=$(du -h "$filepath" | cut -f1)
        echo "   ✅ ${description}: ${SIZE}"
    else
        echo "   ❌ ${description}: MISSING"
        ALL_PASSED=false
    fi
}

check_file "${VERSION}-domain-vertices.txt.gz" "Vertices (domain mapping)"
check_file "${VERSION}-domain.graph" "Forward graph (outlinks)"
check_file "${VERSION}-domain.properties" "Forward graph properties"
check_file "${VERSION}-domain-t.graph" "Transpose graph (backlinks)"
check_file "${VERSION}-domain-t.properties" "Transpose graph properties"
check_file "${VERSION}-domain.stats" "Graph statistics"

# Read stats file if available
echo ""
echo "5. Graph Statistics:"
STATS_FILE="${WEBGRAPH_DIR}/${VERSION}-domain.stats"
if [ -f "$STATS_FILE" ]; then
    NODES=$(grep "^nodes=" "$STATS_FILE" | cut -d= -f2)
    ARCS=$(grep "^arcs=" "$STATS_FILE" | cut -d= -f2)
    if [ -n "$NODES" ]; then
        printf "   ✅ Nodes: %'d\n" "$NODES"
    fi
    if [ -n "$ARCS" ]; then
        printf "   ✅ Edges: %'d\n" "$ARCS"
    fi
fi

# Final verdict
echo ""
echo "============================================================"
if [ "$ALL_PASSED" = true ]; then
    echo "🎉 SETUP COMPLETE!"
    echo "============================================================"
    echo ""
    echo "You're ready to discover domains!"
    exit 0
else
    echo "⚠️ SETUP INCOMPLETE"
    echo "============================================================"
    echo ""
    echo "Please check the failed components above."
    exit 1
fi
