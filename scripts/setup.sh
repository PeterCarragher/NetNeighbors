#!/bin/bash
# Setup script for NetNeighbors discovery notebook
# Installs Java, gcsfuse, clones repos, and builds tools

set -e

echo "============================================================"
echo "           NetNeighbors Environment Setup"
echo "============================================================"
echo ""

# Install Java 17 and Maven
echo "1. Installing Java 17 and Maven..."
apt-get update -qq > /dev/null 2>&1
apt-get install -y -qq openjdk-17-jdk-headless maven > /dev/null 2>&1
echo "   ✅ Java installation complete"
java -version 2>&1 | head -1

# Install gcsfuse for GCS mounting
echo ""
echo "2. Installing gcsfuse..."
apt-get install -y -qq gcsfuse > /dev/null 2>&1
echo "   ✅ gcsfuse installed"

# Clone and build cc-webgraph
echo ""
echo "3. Setting up cc-webgraph..."
if [ ! -d "cc-webgraph" ]; then
    echo "   Cloning cc-webgraph repository..."
    git clone --depth 1 https://github.com/commoncrawl/cc-webgraph.git > /dev/null 2>&1

    echo "   Building cc-webgraph (this may take 1-2 minutes)..."
    cd cc-webgraph
    mvn clean package -DskipTests -q
    cd ..

    echo "   ✅ cc-webgraph built successfully"
else
    echo "   ✅ cc-webgraph already exists"
fi

# Clone NetNeighbors and compile DiscoveryTool
echo ""
echo "4. Setting up NetNeighbors..."
if [ ! -d "NetNeighbors" ]; then
    echo "   Cloning NetNeighbors repository..."
    git clone --depth 1 https://github.com/PeterCarragher/NetNeighbors.git > /dev/null 2>&1

    echo "   Compiling DiscoveryTool..."
    mkdir -p NetNeighbors/bin
    javac -cp "cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar" \
        -d NetNeighbors/bin \
        NetNeighbors/src/DiscoveryTool.java

    echo "   ✅ NetNeighbors tools ready"
else
    echo "   ✅ NetNeighbors already exists"
fi

echo ""
echo "============================================================"
echo "                    Setup Complete!"
echo "============================================================"
