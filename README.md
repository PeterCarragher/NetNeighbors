# NetNeighbors - News Source Discovery

A web application for researchers to discover related news domains using CommonCrawl webgraph analysis.

## Architecture

- **Frontend**: Next.js 13 + TypeScript + Tailwind CSS
- **Backend**: Java 11 + Javalin HTTP server + cc-webgraph
- **Queue/Cache**: Upstash Redis (optional)
- **Graph Data**: CommonCrawl domain-level webgraph

## Project Structure

```
.
├── backend/                 # Java backend (discovery worker)
│   ├── src/main/java/com/discovery/
│   │   ├── Main.java       # HTTP server
│   │   ├── DiscoveryService.java
│   │   └── models/
│   └── pom.xml
├── frontend/               # Next.js frontend
│   ├── app/
│   │   ├── page.tsx
│   │   └── api/discover/route.ts
│   └── components/
│       └── DiscoveryForm.tsx
├── cc-webgraph/            # Submodule: CommonCrawl webgraph tools
├── Dockerfile              # Multi-stage build for backend
└── README.md
```

## Prerequisites

- Java 11+
- Maven 3.6+
- Node.js 18.16+
- CommonCrawl domain webgraph data

## Getting Webgraph Data

Download the domain-level webgraph (~15GB):

```bash
# Create data directory
mkdir -p /path/to/webgraph-data
cd /path/to/webgraph-data

# Download graph files (replace with desired crawl)
GRAPH=cc-main-2024-feb-apr-may-domain
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2024-feb-apr-may/domain/$GRAPH.graph
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2024-feb-apr-may/domain/$GRAPH.properties
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2024-feb-apr-may/domain/$GRAPH-t.graph
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2024-feb-apr-may/domain/$GRAPH-t.properties

# Download and build vertex map
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2024-feb-apr-may/domain/$GRAPH-vertices.txt.gz
# Then run the vertex map builder (see cc-webgraph docs)
```

## Local Development

### 1. Build cc-webgraph

```bash
cd cc-webgraph
mvn clean install -DskipTests
cd ..
```

### 2. Build and Run Backend

```bash
cd backend
mvn clean package -DskipTests

# Run (replace GRAPH_PATH with your data location)
GRAPH_PATH=/path/to/webgraph-data/cc-main-2024-feb-apr-may-domain \
java -Xmx8g -jar target/discovery-worker-1.0-SNAPSHOT.jar
```

The backend will start on port 8080.

### 3. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on http://localhost:3000.

### 4. Environment Variables

**Backend:**
- `GRAPH_PATH` - Path to webgraph files (required)
- `PORT` - HTTP port (default: 8080)
- `UPSTASH_REDIS_REST_URL` - Redis URL (optional)
- `UPSTASH_REDIS_REST_TOKEN` - Redis token (optional)

**Frontend:**
- `BACKEND_URL` - Backend service URL (default: http://localhost:8080)

## Production Deployment

### Backend (Google Cloud Run)

```bash
# Build and push Docker image
docker build -t gcr.io/YOUR_PROJECT/discovery-worker .
docker push gcr.io/YOUR_PROJECT/discovery-worker

# Deploy to Cloud Run
gcloud run deploy discovery-worker \
  --image gcr.io/YOUR_PROJECT/discovery-worker \
  --region us-central1 \
  --memory 16Gi \
  --cpu 4 \
  --timeout 3600s \
  --set-env-vars "GRAPH_PATH=/data/webgraph/cc-main-2024-domain" \
  --allow-unauthenticated
```

Note: You'll need to mount the webgraph data via GCS FUSE or include it in the image.

### Frontend (Vercel)

1. Push the frontend directory to GitHub
2. Import in Vercel
3. Set environment variable: `BACKEND_URL=https://your-cloud-run-url`
4. Deploy

## API Endpoints

### POST /discover

Request:
```json
{
  "domain": "example.com",
  "threshold": 2,
  "direction": "outgoing"
}
```

Response:
```json
{
  "jobId": "uuid",
  "status": "completed",
  "domain": "example.com",
  "direction": "outgoing",
  "threshold": 2,
  "results": [
    {"domain": "related-site.com", "count": 150},
    {"domain": "another-site.org", "count": 45}
  ],
  "totalFound": 234,
  "processingTimeMs": 1523
}
```

### GET /health

Returns server status and whether the graph is loaded.

## License

This project uses the [cc-webgraph](https://github.com/commoncrawl/cc-webgraph) library, which is Apache 2.0 licensed.
