# Stage 1: Build cc-webgraph uber-JAR
FROM maven:3.9-eclipse-temurin-17 AS builder

RUN git clone --depth 1 https://github.com/commoncrawl/cc-webgraph.git /build/cc-webgraph
WORKDIR /build/cc-webgraph
RUN mvn clean package -DskipTests -q

# Compile DiscoveryTool in the builder stage (has JDK)
COPY src/ /build/src/
RUN mkdir -p /build/bin && \
    javac -cp /build/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar \
        -d /build/bin /build/src/DiscoveryTool.java


# Stage 2: Runtime (JRE only, no compiler needed)
FROM eclipse-temurin:17-jre

# Install Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy cc-webgraph JAR and compiled classes from builder
COPY --from=builder /build/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar /app/cc-webgraph.jar
COPY --from=builder /build/bin/ /app/bin/

# Install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application
COPY graph_bridge.py discovery_network_vis.py utils.py webgraph_discovery.py /app/
COPY assets/ /app/assets/

# Environment
ENV CC_WEBGRAPH_JAR=/app/cc-webgraph.jar
ENV WEBGRAPH_DIR=/data/webgraph
ENV WEBGRAPH_VERSION=cc-main-2024-feb-apr-may
ENV PORT=8050

EXPOSE 8050

CMD ["python3", "discovery_network_vis.py"]
