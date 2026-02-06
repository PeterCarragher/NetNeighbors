#!/bin/bash
# Setup script for NetNeighbors discovery notebook
# Installs Java, gcsfuse, clones repos, and builds tools
#
# Usage:
#   ./setup.sh                    # Auto-detect environment (Colab or local)
#   ./setup.sh --local            # Skip apt-get installs (for local dev)
#   ./setup.sh --base-dir /path   # Specify base directory

set -e

# Parse arguments
LOCAL_MODE=false
BASE_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            LOCAL_MODE=true
            shift
            ;;
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Auto-detect base directory
if [ -z "$BASE_DIR" ]; then
    if [ -d "/content" ]; then
        BASE_DIR="/content"
    else
        # Use the directory containing this script's parent
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
        LOCAL_MODE=true  # Auto-enable local mode if not in Colab
    fi
fi

# Determine NetNeighbors directory (might be submodule or will be cloned)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETNEIGHBORS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================================"
echo "           NetNeighbors Environment Setup"
echo "============================================================"
echo "Base directory: $BASE_DIR"
echo "NetNeighbors: $NETNEIGHBORS_DIR"
echo "Mode: $([ "$LOCAL_MODE" = true ] && echo 'local' || echo 'Colab')"
echo ""

cd "$BASE_DIR"

# Install or check Java 17 and Maven
echo "1. Setting up Java 17 and Maven..."

if [ "$LOCAL_MODE" = false ]; then
    # Colab - install directly via apt-get (no sudo needed)
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq openjdk-17-jdk-headless maven > /dev/null 2>&1
    echo "   ✅ Java and Maven installed"
else
    # Local mode - check if installed, give instructions if not
    MISSING=""
    if ! command -v javac &> /dev/null; then
        MISSING="JDK 17+"
    fi
    if ! command -v mvn &> /dev/null; then
        [ -n "$MISSING" ] && MISSING="$MISSING and "
        MISSING="${MISSING}Maven"
    fi

    if [ -n "$MISSING" ]; then
        echo ""
        echo "   ❌ Missing: $MISSING"
        echo ""
        echo "   Please install before running this notebook:"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "     sudo apt install openjdk-17-jdk maven"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "     brew install openjdk@17 maven"
        else
            echo "     Install JDK 17+ and Maven for your platform"
        fi
        echo ""
        exit 1
    fi
    echo "   ✅ Java and Maven already installed"
fi
java -version 2>&1 | head -1

# Install gcsfuse for GCS mounting (Colab only)
if [ "$LOCAL_MODE" = false ]; then
    echo ""
    echo "2. Installing gcsfuse..."
    if ! command -v gcsfuse &> /dev/null; then
        # Add Google Cloud apt repository for gcsfuse
        export GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s)
        echo "deb https://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list > /dev/null
        curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - > /dev/null 2>&1
        apt-get update -qq > /dev/null 2>&1
        apt-get install -y -qq gcsfuse > /dev/null 2>&1
        echo "   ✅ gcsfuse installed"
    else
        echo "   ✅ gcsfuse already installed"
    fi
else
    echo ""
    echo "2. Skipping gcsfuse (local mode, not needed)"
fi

# Install Python dependencies
echo ""
echo "3. Installing Python dependencies..."
if command -v pip &> /dev/null; then
    pip install -q psutil tqdm pandas ipywidgets 2>/dev/null || pip install --user -q psutil tqdm pandas ipywidgets
    echo "   ✅ Python dependencies installed"
elif command -v pip3 &> /dev/null; then
    pip3 install -q psutil tqdm pandas ipywidgets 2>/dev/null || pip3 install --user -q psutil tqdm pandas ipywidgets
    echo "   ✅ Python dependencies installed"
else
    echo "   ⚠️  pip not found, skipping Python dependencies"
    echo "   You may need to run: pip install psutil tqdm pandas ipywidgets"
fi

# Clone and build cc-webgraph
echo ""
echo "4. Setting up cc-webgraph..."
if [ ! -d "$BASE_DIR/cc-webgraph" ]; then
    echo "   Cloning cc-webgraph repository..."
    git clone --depth 1 https://github.com/commoncrawl/cc-webgraph.git "$BASE_DIR/cc-webgraph" > /dev/null 2>&1
fi

CC_WEBGRAPH_JAR="$BASE_DIR/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar"
if [ ! -f "$CC_WEBGRAPH_JAR" ]; then
    echo "   Building cc-webgraph (this may take 1-2 minutes)..."
    cd "$BASE_DIR/cc-webgraph"
    mvn clean package -DskipTests -q
    cd "$BASE_DIR"
    echo "   ✅ cc-webgraph built successfully"
else
    echo "   ✅ cc-webgraph already built"
fi

# Setup NetNeighbors and compile DiscoveryTool
echo ""
echo "5. Setting up NetNeighbors..."

# Clone if not present (Colab mode) - but might already exist as submodule
if [ ! -d "$BASE_DIR/NetNeighbors" ] && [ "$NETNEIGHBORS_DIR" != "$BASE_DIR/NetNeighbors" ]; then
    echo "   Cloning NetNeighbors repository..."
    git clone --depth 1 https://github.com/PeterCarragher/NetNeighbors.git "$BASE_DIR/NetNeighbors" > /dev/null 2>&1
    NETNEIGHBORS_DIR="$BASE_DIR/NetNeighbors"
fi

# Compile DiscoveryTool if missing or source is newer
DISCOVERY_CLASS="$NETNEIGHBORS_DIR/bin/DiscoveryTool.class"
DISCOVERY_SRC="$NETNEIGHBORS_DIR/src/DiscoveryTool.java"

NEEDS_COMPILE=false
if [ ! -f "$DISCOVERY_CLASS" ]; then
    NEEDS_COMPILE=true
elif [ "$DISCOVERY_SRC" -nt "$DISCOVERY_CLASS" ]; then
    echo "   Source file updated, recompiling..."
    NEEDS_COMPILE=true
fi

if [ "$NEEDS_COMPILE" = true ]; then
    echo "   Compiling DiscoveryTool..."
    mkdir -p "$NETNEIGHBORS_DIR/bin"
    javac -cp "$CC_WEBGRAPH_JAR" \
        -d "$NETNEIGHBORS_DIR/bin" \
        "$NETNEIGHBORS_DIR/src/DiscoveryTool.java"
    echo "   ✅ DiscoveryTool compiled"
else
    echo "   ✅ DiscoveryTool already compiled"
fi

echo ""
echo "============================================================"
echo "                    Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Download webgraph data (use utils.download_webgraph)"
echo "  2. Run verify.sh to confirm installation"
