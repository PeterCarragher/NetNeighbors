# Build stage
FROM maven:3.9-eclipse-temurin-17 AS build

# Build cc-webgraph first and install to local repo
WORKDIR /build/cc-webgraph
COPY cc-webgraph/ .
RUN mvn clean install -DskipTests -q

# Build the discovery worker
WORKDIR /build/backend
COPY backend/pom.xml .
COPY backend/src ./src
RUN mvn clean package -DskipTests -q

# Runtime stage
FROM eclipse-temurin:17-jre

WORKDIR /app

# Copy the built JAR (shaded uber-jar includes all dependencies)
COPY --from=build /build/backend/target/discovery-worker-1.0-SNAPSHOT.jar ./app.jar

# Create data directory
RUN mkdir -p /data/webgraph

# Expose port
EXPOSE 8080

# Set default environment variables
ENV PORT=8080
ENV GRAPH_PATH=/data/webgraph/cc-main-2024-domain

# Run with increased heap for graph processing
CMD ["java", "-Xmx14g", "-jar", "app.jar"]
