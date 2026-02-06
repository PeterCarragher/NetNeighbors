# NetNeighbors Gradio App - Docker Image for Cloud Run
#
# Build: docker build -t netneighbors .
# Run:   docker run -p 7860:7860 -v /path/to/webgraph:/data/webgraph netneighbors

FROM python:3.11-slim

# Install Java 17 and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    maven \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Java home
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone and build cc-webgraph
RUN git clone --depth 1 https://github.com/commoncrawl/cc-webgraph.git /app/cc-webgraph \
    && cd /app/cc-webgraph \
    && mvn clean package -DskipTests -q \
    && rm -rf ~/.m2

# Set cc-webgraph JAR path
ENV CC_WEBGRAPH_JAR=/app/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar

# Copy application code
COPY graph_bridge.py .
COPY app.py .

# Default environment variables (override at runtime)
ENV WEBGRAPH_DIR=/data/webgraph
ENV WEBGRAPH_VERSION=cc-main-2024-feb-apr-may
ENV PORT=7860

# Expose the port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the app
CMD ["python", "app.py"]
