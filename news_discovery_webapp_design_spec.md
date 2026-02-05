# News Source Discovery Webapp - Design Specification

**Project:** Misinformation Domain Discovery System  
**Version:** 1.0  
**Date:** February 5, 2026  
**Author:** Based on Carragher et al. (ICWSM 2024, ACM TIST 2025)

---

## Executive Summary

This document specifies the design for a web application that enables researchers to discover potentially related news domains using webgraph analysis on CommonCrawl data. The system implements the discovery methodology from peer-reviewed research on misinformation detection without requiring users to manually execute code.

**Key Features:**
- Web-based interface for submitting seed domain lists
- Automated discovery using CommonCrawl webgraph (93.9M domains, 1.6B edges)
- Flexible threshold configuration (count-based or percentage-based)
- Bidirectional analysis (backlinks and outlinks)
- Asynchronous processing for large datasets
- CSV export functionality

**Target Users:** Academic researchers, fact-checkers, misinformation analysts

**Expected Volume:** ~100 queries/month

**Budget Constraint:** $0-20/month (leveraging GCloud credits)

---

## Table of Contents

1. [Requirements](#1-requirements)
2. [Architecture Decisions](#2-architecture-decisions)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture](#4-system-architecture)
5. [Data Model](#5-data-model)
6. [Component Specifications](#6-component-specifications)
7. [API Specifications](#7-api-specifications)
8. [Deployment Strategy](#8-deployment-strategy)
9. [Cost Analysis](#9-cost-analysis)
10. [Maintenance & Updates](#10-maintenance--updates)
11. [Security Considerations](#11-security-considerations)
12. [Testing Strategy](#12-testing-strategy)
13. [Future Enhancements](#13-future-enhancements)

---

## 1. Requirements

### 1.1 Functional Requirements

**FR1: Seed Domain Input**
- Users can submit 1-1000 domain names
- Input format: one domain per line
- Validation: basic domain format checking
- Real-time count of entered domains

**FR2: Discovery Configuration**
- **Threshold Type Selection:**
  - Option A: Minimum number of connections (N domains from seed list)
  - Option B: Minimum percentage of backlinks from seed list
- **Direction Selection:**
  - Backlinks: Find domains that link TO the seed list
  - Outlinks: Find domains the seed list links TO

**FR3: Asynchronous Processing**
- System handles any size seed list
- Processing time: 1-10 minutes expected
- User receives job ID immediately
- Frontend polls for results every 2 seconds
- Timeout after 6 minutes with helpful error message

**FR4: Results Display**
- Table showing discovered domains with:
  - Domain name
  - Connection count
  - Percentage (if applicable)
- Sort by connection count (descending)
- CSV export functionality

**FR5: Quarterly Webgraph Updates**
- System must be updatable with new CommonCrawl webgraph releases
- Update process should not require code changes
- Minimal downtime during updates

### 1.2 Non-Functional Requirements

**NFR1: Performance**
- Job submission response: < 5 seconds
- Processing time: Accept up to 60 minutes for large seed lists
- Frontend load time: < 3 seconds

**NFR2: Scalability**
- Handle up to 100 concurrent queries/month
- Support seed lists up to 1000 domains
- Worker can process webgraph of ~100M domains

**NFR3: Reliability**
- 99% uptime for frontend
- Job failure rate < 5%
- Results cached for 1 hour

**NFR4: Usability**
- Intuitive single-page interface
- Clear error messages
- No registration required
- Mobile-responsive design

**NFR5: Cost Efficiency**
- Total monthly cost < $20
- Preferably under $5/month with GCloud credits
- Serverless architecture to minimize idle costs

---

## 2. Architecture Decisions

### 2.1 Why NOT Vercel + Node.js for Backend?

**Decision:** Use Cloud Run (Java) instead of Vercel serverless functions

**Rationale:**
1. **Timeout Constraints:** Vercel serverless functions limited to 5 min (Enterprise), but graph queries may take longer
2. **Memory Limitations:** Max 3GB on Vercel Enterprise vs 16GB+ on Cloud Run
3. **Existing Codebase:** cc-webgraph repository is Java-based using WebGraph framework
4. **Cold Starts:** Loading 22.5GB webgraph on each serverless invocation is impractical
5. **Cost:** Cloud Run only charges for actual processing time

### 2.2 Why Cloud Run Over Other Options?

**Decision:** Google Cloud Run for backend worker

**Alternatives Considered:**

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Cloud Run (CHOSEN)** | 60min timeout, 16GB RAM, scales to zero, Java support | Requires containerization | ~$0.10/month |
| Neo4j Graph DB | Purpose-built for graphs, Cypher queries | $65+/month, vendor lock-in | Too expensive |
| Railway/Render | Simple deployment | Limited by existing credits | $5-20/month |
| EC2/Compute Engine | Full control | Always-on costs, manual scaling | $10+/month |

**Winner:** Cloud Run provides the perfect balance of:
- Generous resource limits (60min timeout, 16GB RAM)
- Pay-per-use pricing (scales to zero)
- Native GCP integration (GCS, Secret Manager)
- Compatible with existing Java/Maven codebase

### 2.3 Why Upstash Redis?

**Decision:** Upstash Redis for job queue and result caching

**Rationale:**
1. **Serverless-friendly:** REST API works with Vercel and Cloud Run
2. **Free tier:** 10,000 commands/day sufficient for 100 queries/month
3. **Durable:** Results persisted with TTL
4. **Simple:** No need for complex message queue infrastructure
5. **Global:** Low latency from Vercel edge functions

**Alternatives:** Cloud Tasks (more complex), Cloud Pub/Sub (overkill for low volume)

### 2.4 Data Storage Strategy

**Decision:** Store webgraph files in Google Cloud Storage (GCS)

**Rationale:**
1. **Cost:** $0.50/month for 22.5GB
2. **Accessibility:** Worker downloads on startup or mounts via FUSE
3. **Versioning:** Easy to maintain multiple webgraph versions
4. **Integration:** Native Cloud Run integration

**Storage Format:**
- Raw CommonCrawl files: `.txt.gz` (vertices and edges)
- Optional: Pre-processed BVGraph format for faster loading
- Organized by version: `gs://bucket/2025-26/vertices.txt.gz`

---

## 3. Technology Stack

### 3.1 Frontend

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Framework** | Next.js | 14.1+ | React-based, Vercel-optimized, App Router |
| **Language** | TypeScript | 5.3+ | Type safety, better DX |
| **Styling** | Tailwind CSS | 3.4+ | Rapid UI development, responsive |
| **HTTP Client** | Fetch API | Native | Built-in, no dependencies |
| **Validation** | Zod | 3.22+ | Runtime type checking |
| **State Management** | React Hooks | Native | Simple requirements, no need for Redux |
| **Hosting** | Vercel | - | Free tier, excellent Next.js support |

### 3.2 Backend

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Runtime** | Java | 17 LTS | WebGraph framework requirement |
| **Build Tool** | Maven | 3.9+ | Standard Java dependency management |
| **Web Framework** | Javalin | 5.6+ | Lightweight, REST API support |
| **Graph Library** | WebGraph | 3.6+ | Optimized for large graphs, used in cc-webgraph |
| **Redis Client** | Jedis | 5.0+ | Mature, thread-safe Redis client |
| **JSON** | Gson | 2.10+ | JSON serialization/deserialization |
| **Hosting** | Cloud Run | - | Containerized, auto-scaling |

### 3.3 Infrastructure

| Component | Service | Purpose |
|-----------|---------|---------|
| **Job Queue** | Upstash Redis | Job status tracking, result caching |
| **Storage** | Google Cloud Storage | Webgraph data (22.5GB) |
| **Secrets** | GCP Secret Manager | API credentials, Redis tokens |
| **Container Registry** | Google Container Registry | Docker images |
| **Monitoring** | Cloud Logging | Error tracking, performance monitoring |

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER BROWSER                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Next.js Frontend (React)                 │    │
│  │  - Domain input form                                │    │
│  │  - Configuration options                            │    │
│  │  - Results display + CSV export                     │    │
│  └────────────────┬───────────────────────────────────┘    │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    │ HTTP POST /api/discover
                    │ HTTP GET /api/discover?jobId=xxx
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                    VERCEL (API ROUTES)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  /api/discover                                      │    │
│  │  - Validate input                                   │    │
│  │  - Generate job ID                                  │    │
│  │  - Trigger Cloud Run worker                         │    │
│  │  - Poll job status                                  │    │
│  └────────────────┬───────────────────────────────────┘    │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    │ ① Store job metadata
                    │ ② Retrieve results
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                    UPSTASH REDIS                             │
│                                                              │
│  Keys:                                                       │
│  - job:{jobId}      → Job status (queued/processing/complete)│
│  - result:{jobId}   → Discovery results (TTL: 1 hour)       │
│                                                              │
└───────────────────┬──────────────────────────────────────────┘
                    ↑
                    │ ③ Update job status
                    │ ④ Store results
                    │
┌─────────────────────────────────────────────────────────────┐
│              GOOGLE CLOUD RUN (WORKER)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Java Application (Container)                       │    │
│  │                                                      │    │
│  │  POST /discover:                                     │    │
│  │  1. Load webgraph from GCS (cached)                 │    │
│  │  2. Convert seed domains → node IDs                 │    │
│  │  3. Run discovery algorithm:                        │    │
│  │     - For each seed: get neighbors (successors/     │    │
│  │       predecessors)                                  │    │
│  │     - Count connections per candidate               │    │
│  │     - Filter by threshold                           │    │
│  │  4. Store results in Redis                          │    │
│  │  5. Update job status                               │    │
│  │                                                      │    │
│  │  GET /health: Health check endpoint                 │    │
│  └────────────────┬───────────────────────────────────┘    │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    │ ⑤ Read webgraph data
                    ↓
┌─────────────────────────────────────────────────────────────┐
│              GOOGLE CLOUD STORAGE                            │
│                                                              │
│  Bucket: your-webgraph-bucket                                │
│  ├── 2025-26/                                                │
│  │   ├── vertices.txt.gz  (domain list with IDs)            │
│  │   └── edges.txt.gz     (edge list)                       │
│  ├── 2025-40/                                                │
│  │   └── ...              (next quarter release)            │
│  └── current → 2025-26/   (symlink to active version)       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Request Flow

**Flow 1: Job Submission**
```
1. User submits form (domains + config)
2. Frontend validates input
3. POST to /api/discover
4. API generates jobId (nanoid)
5. API stores job metadata in Redis
6. API triggers Cloud Run worker via HTTP POST
7. Worker responds immediately (non-blocking)
8. API returns jobId to frontend
9. Frontend starts polling
```

**Flow 2: Discovery Processing (Cloud Run)**
```
1. Worker receives job request
2. Load webgraph (if not cached):
   - Download vertices.txt.gz from GCS
   - Download edges.txt.gz from GCS
   - Build in-memory graph structure
3. Parse seed domains
4. For each seed domain:
   - Look up node ID in vertex map
   - Get neighbors (predecessors for backlinks, successors for outlinks)
   - Increment connection count for each neighbor
5. Filter candidates by threshold:
   - Count-based: count >= minBacklinks
   - Percent-based: (count / total_backlinks) >= minPercent
6. Sort by connection count (descending)
7. Serialize results to JSON
8. Store in Redis with key result:{jobId}
9. Update job status to "complete"
```

**Flow 3: Result Polling**
```
1. Frontend polls GET /api/discover?jobId=xxx every 2s
2. API checks Redis for result:{jobId}
3. If found: return result + status=complete
4. If not found: check job:{jobId} status
5. Return current status (processing/failed)
6. Frontend displays results or continues polling
7. Timeout after 6 minutes → display error
```

### 4.3 Data Flow Diagram

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Vercel  │────────▶│  Upstash │◀────────│ Cloud Run│
│ Frontend │  write  │  Redis   │  write  │  Worker  │
│          │◀────────│          │────────▶│          │
└──────────┘   read  └──────────┘   read  └─────┬────┘
                                                  │
                                                  │ read
                                                  ↓
                                            ┌──────────┐
                                            │   GCS    │
                                            │ Webgraph │
                                            └──────────┘
```

---

## 5. Data Model

### 5.1 Redis Data Structures

**Key: `job:{jobId}`**
```json
{
  "status": "queued" | "processing" | "complete" | "failed",
  "createdAt": "2026-02-05T10:30:00Z",
  "domains": 150,
  "error": "Optional error message"
}
```
- TTL: 3600 seconds (1 hour)
- Purpose: Track job lifecycle

**Key: `result:{jobId}`**
```json
{
  "discovered": [
    {
      "domain": "discovered-site.com",
      "count": 8,
      "percentage": 5.3
    }
  ],
  "totalSeedDomains": 150,
  "queriedAt": "2026-02-05T10:35:22Z",
  "webgraphVersion": "2025-26"
}
```
- TTL: 3600 seconds (1 hour)
- Purpose: Cache discovery results

### 5.2 Webgraph Data Format

**CommonCrawl Format (Source):**

`vertices.txt.gz`:
```
0	com.example
1	org.wikipedia
2	net.test
...
```
- Tab-separated: `{node_id}\t{reversed_domain}`
- Sorted lexicographically by reversed domain

`edges.txt.gz`:
```
0	1
0	2
1	0
...
```
- Tab-separated: `{from_id}\t{to_id}`
- Sorted numerically by from_id, then to_id

**In-Memory Structure (Java):**
```java
// Domain name → Node ID mapping
Map<String, Long> domainToId = new HashMap<>();

// BVGraph for efficient neighbor queries
BVGraph graph = BVGraph.load(graphPath);

// Node ID → Domain name (for reverse lookup)
String[] idToDomain = new String[numNodes];
```

### 5.3 API Request/Response Models

**POST /api/discover Request:**
```typescript
{
  domains: string[],              // 1-1000 domains
  minBacklinks?: number,          // 1-1000 (if count-based)
  minBacklinksPercent?: number,   // 1-100 (if percent-based)
  direction: 'backlinks' | 'outlinks'
}
```

**POST /api/discover Response:**
```typescript
{
  jobId: string  // "abc123xyz"
}
```

**GET /api/discover?jobId=xxx Response:**
```typescript
{
  status: 'queued' | 'processing' | 'complete' | 'failed',
  data?: DiscoveryResult,   // Only if complete
  message?: string          // Only if failed
}
```

---

## 6. Component Specifications

### 6.1 Frontend Components

#### 6.1.1 `app/page.tsx`
**Purpose:** Landing page with form and results

**Features:**
- Hero section with title and description
- DiscoveryForm component
- Footer with research citations

#### 6.1.2 `components/DiscoveryForm.tsx`
**Purpose:** Main discovery interface

**State:**
```typescript
- domains: string                    // Textarea content
- thresholdType: 'count' | 'percent' // Radio selection
- minBacklinks: number               // Count threshold
- minPercent: number                 // Percent threshold
- direction: 'backlinks' | 'outlinks'
- jobId: string | null
- results: DiscoveryResult | null
- status: 'idle' | 'submitting' | 'processing' | 'complete' | 'error'
- errorMessage: string
```

**Functions:**
- `handleSubmit()`: Validate and submit job
- `pollResults(jobId)`: Poll every 2s until complete
- `exportCSV()`: Download results as CSV

**UI Elements:**
- Textarea: Domain input (48 lines high, monospace)
- Radio buttons: Backlinks vs Outlinks
- Radio buttons: Count vs Percent threshold
- Number inputs: Threshold values
- Submit button: With loading spinner
- Results table: Sortable, paginated
- Export button: CSV download

#### 6.1.3 `app/api/discover/route.ts`
**Purpose:** API route for discovery operations

**POST Handler:**
1. Validate request with Zod
2. Generate jobId
3. Store job metadata in Redis
4. Trigger Cloud Run worker (5s timeout)
5. Return jobId

**GET Handler:**
1. Extract jobId from query params
2. Check Redis for result
3. Return status + data

**Error Handling:**
- 400: Invalid input
- 404: Job not found
- 500: Worker failure

### 6.2 Backend Components

#### 6.2.1 `DiscoveryWorker.java`
**Purpose:** Main worker application

**Methods:**
```java
public void initialize() {
  // Load webgraph from GCS
  // Build domainToId map
  // Initialize BVGraph
}

public DiscoveryResult runDiscovery(DiscoveryRequest request) {
  // Convert seed domains to IDs
  // Execute discovery algorithm
  // Return results
}
```

**Algorithm (from paper):**
```java
Set<Long> seedIds = getSeedIds(request.seedDomains);
Map<Long, Integer> candidateCounts = new HashMap<>();

for (Long seedId : seedIds) {
  LazyLongIterator neighbors = request.isBacklinks 
    ? graph.predecessors(seedId)  // Who links to this seed
    : graph.successors(seedId);    // Who this seed links to
    
  long neighbor;
  while ((neighbor = neighbors.nextLong()) != -1) {
    candidateCounts.merge(neighbor, 1, Integer::sum);
  }
}

// Filter by threshold
List<DiscoveredDomain> results = candidateCounts.entrySet().stream()
  .filter(e -> e.getValue() >= threshold)
  .map(e -> new DiscoveredDomain(idToDomain[(int)e.getKey()], e.getValue()))
  .sorted(Comparator.comparing(DiscoveredDomain::getCount).reversed())
  .collect(Collectors.toList());
```

#### 6.2.2 `Main.java`
**Purpose:** HTTP server entry point

**Endpoints:**
- `POST /discover`: Receive job, execute discovery, store result
- `GET /health`: Health check for Cloud Run

**Implementation:**
```java
public static void main(String[] args) {
  DiscoveryWorker worker = new DiscoveryWorker();
  worker.initialize(); // Load graph once at startup
  
  Javalin app = Javalin.create().start(8080);
  
  app.post("/discover", ctx -> {
    DiscoveryRequest req = ctx.bodyAsClass(DiscoveryRequest.class);
    
    // Update status to processing
    updateJobStatus(req.getJobId(), "processing");
    
    // Run discovery
    DiscoveryResult result = worker.runDiscovery(req);
    
    // Store result in Redis
    storeResult(req.getJobId(), result);
    
    ctx.json(Map.of("status", "complete"));
  });
  
  app.get("/health", ctx -> ctx.result("OK"));
}
```

#### 6.2.3 `Dockerfile`
**Purpose:** Container definition for Cloud Run

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre
WORKDIR /app

# Copy JAR
COPY --from=build /app/target/*.jar ./app.jar

# Install gcloud SDK (for GCS access)
RUN apt-get update && apt-get install -y curl
RUN curl https://sdk.cloud.google.com | bash

# Expose port
EXPOSE 8080

# Allocate heap memory (14GB for 16GB instance)
CMD ["java", "-Xmx14g", "-jar", "app.jar"]
```

---

## 7. API Specifications

### 7.1 Frontend API (Vercel)

#### POST /api/discover

**Description:** Submit a discovery job

**Request:**
```http
POST /api/discover HTTP/1.1
Content-Type: application/json

{
  "domains": [
    "example.com",
    "test.org",
    "sample.net"
  ],
  "minBacklinks": 5,
  "direction": "backlinks"
}
```

**Response (Success):**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jobId": "V1StGXR8_Z5jdHi6B-myT"
}
```

**Response (Error):**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Invalid request",
  "details": {
    "domains": {
      "_errors": ["Array must contain at least 1 element(s)"]
    }
  }
}
```

#### GET /api/discover?jobId={jobId}

**Description:** Check job status and retrieve results

**Request:**
```http
GET /api/discover?jobId=V1StGXR8_Z5jdHi6B-myT HTTP/1.1
```

**Response (Processing):**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "processing"
}
```

**Response (Complete):**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "complete",
  "data": {
    "discovered": [
      {
        "domain": "discovered-site.com",
        "count": 8,
        "percentage": 2.67
      },
      {
        "domain": "another-domain.org",
        "count": 6,
        "percentage": 2.0
      }
    ],
    "totalSeedDomains": 3,
    "queriedAt": "2026-02-05T10:35:22Z",
    "webgraphVersion": "2025-26"
  }
}
```

**Response (Failed):**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "failed",
  "message": "Failed to load webgraph data"
}
```

### 7.2 Backend API (Cloud Run)

#### POST /discover

**Description:** Execute discovery algorithm

**Request:**
```http
POST /discover HTTP/1.1
Content-Type: application/json

{
  "jobId": "V1StGXR8_Z5jdHi6B-myT",
  "seedDomains": ["example.com", "test.org"],
  "minBacklinks": 5,
  "minBacklinksPercent": null,
  "isBacklinks": true
}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "complete",
  "jobId": "V1StGXR8_Z5jdHi6B-myT"
}
```

**Error Responses:**
- 500: Internal server error (graph loading failure, etc.)
- 503: Service unavailable (startup in progress)

#### GET /health

**Description:** Health check

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/plain

OK
```

---

## 8. Deployment Strategy

### 8.1 Prerequisites

**Required Accounts:**
- Google Cloud account with billing enabled
- Upstash account (free tier)
- Vercel account (free tier)
- GitHub account (for CI/CD)

**Required Tools:**
- gcloud CLI
- Docker
- Node.js 18+
- Java 17+ & Maven
- Git

### 8.2 Initial Setup

**Step 1: GCP Project Setup**
```bash
# Create project
gcloud projects create news-discovery-prod --name="News Discovery"
gcloud config set project news-discovery-prod

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create service account
gcloud iam service-accounts create discovery-worker \
  --display-name="Discovery Worker"

# Grant permissions
gcloud projects add-iam-policy-binding news-discovery-prod \
  --member="serviceAccount:discovery-worker@news-discovery-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

**Step 2: Create GCS Bucket**
```bash
# Create bucket
gsutil mb -c STANDARD -l us-central1 gs://news-discovery-webgraph

# Download CommonCrawl webgraph
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2025-26-nov-dec-jan/domain/cc-main-2025-26-nov-dec-jan-domain-vertices.txt.gz
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2025-26-nov-dec-jan/domain/cc-main-2025-26-nov-dec-jan-domain-edges.txt.gz

# Upload to GCS
gsutil -m cp *.txt.gz gs://news-discovery-webgraph/2025-26/
```

**Step 3: Upstash Redis Setup**
```bash
# Create database at https://console.upstash.com
# Note down:
# - UPSTASH_REDIS_REST_URL
# - UPSTASH_REDIS_REST_TOKEN
```

**Step 4: Store Secrets**
```bash
# Store Upstash credentials in Secret Manager
echo -n "https://your-endpoint.upstash.io" | \
  gcloud secrets create upstash-url --data-file=-

echo -n "your_token_here" | \
  gcloud secrets create upstash-token --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding upstash-url \
  --member="serviceAccount:discovery-worker@news-discovery-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding upstash-token \
  --member="serviceAccount:discovery-worker@news-discovery-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 8.3 Backend Deployment (Cloud Run)

**Build and Deploy:**
```bash
cd backend

# Build Docker image
docker build -t gcr.io/news-discovery-prod/discovery-worker:latest .

# Push to GCR
docker push gcr.io/news-discovery-prod/discovery-worker:latest

# Deploy to Cloud Run
gcloud run deploy discovery-worker \
  --image gcr.io/news-discovery-prod/discovery-worker:latest \
  --platform managed \
  --region us-central1 \
  --memory 16Gi \
  --cpu 4 \
  --timeout 3600s \
  --max-instances 3 \
  --min-instances 0 \
  --allow-unauthenticated \
  --service-account discovery-worker@news-discovery-prod.iam.gserviceaccount.com \
  --set-env-vars "GCS_BUCKET=news-discovery-webgraph,WEBGRAPH_VERSION=2025-26" \
  --set-secrets "UPSTASH_REDIS_URL=upstash-url:latest,UPSTASH_REDIS_TOKEN=upstash-token:latest"

# Get Cloud Run URL
gcloud run services describe discovery-worker \
  --region us-central1 \
  --format 'value(status.url)'
```

**Note down Cloud Run URL:** `https://discovery-worker-xxxxx-uc.a.run.app`

### 8.4 Frontend Deployment (Vercel)

**Option A: Vercel CLI**
```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Set environment variables
vercel env add UPSTASH_REDIS_REST_URL production
vercel env add UPSTASH_REDIS_REST_TOKEN production
vercel env add CLOUD_RUN_WORKER_URL production

# Deploy
vercel --prod
```

**Option B: GitHub Integration**
1. Push code to GitHub
2. Import repository in Vercel dashboard
3. Add environment variables in Vercel project settings
4. Vercel auto-deploys on push to main branch

### 8.5 CI/CD Pipeline (Optional)

**GitHub Actions for Backend:**
```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      
      - name: Build and Push
        run: |
          cd backend
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/discovery-worker
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy discovery-worker \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/discovery-worker \
            --region us-central1 \
            --platform managed
```

---

## 9. Cost Analysis

### 9.1 Monthly Cost Breakdown

**With 100 queries/month, average 2 minutes processing per query:**

| Service | Usage | Unit Cost | Monthly Cost |
|---------|-------|-----------|--------------|
| **Google Cloud Storage** | 22.5 GB storage | $0.020/GB | **$0.45** |
| **Cloud Run** | 200 CPU-minutes, 3.2 GB-hours | $0.00002400/CPU-sec, $0.00000250/GB-sec | **$0.10** |
| **GCR (Container Registry)** | ~2 GB image | $0.026/GB | **$0.05** |
| **Upstash Redis (Free Tier)** | 10k commands/day (sufficient) | Free | **$0.00** |
| **Vercel (Free Tier)** | <100 GB bandwidth | Free | **$0.00** |
| **Total** | | | **~$0.60/month** |

### 9.2 Cost Scaling

**At 1,000 queries/month:**
- Cloud Run: $1.00
- GCS: $0.45
- **Total: ~$1.45/month**

**At 10,000 queries/month:**
- Cloud Run: $10.00
- Upstash: $10/month (paid tier)
- GCS: $0.45
- **Total: ~$20.45/month**

### 9.3 Cost Optimization Tips

1. **Use Cloud Run min-instances=0** to scale to zero during idle periods
2. **Cache webgraph in memory** if processing many jobs consecutively
3. **Compress results** before storing in Redis to save space
4. **Set aggressive TTLs** on Redis keys (1 hour for results)
5. **Use GCS lifecycle policies** to delete old webgraph versions

---

## 10. Maintenance & Updates

### 10.1 Quarterly Webgraph Update Process

**CommonCrawl releases new webgraphs every ~3 months. Update procedure:**

**Automated Update Script (`scripts/update-webgraph.sh`):**
```bash
#!/bin/bash
set -e

VERSION=$1  # e.g., "2025-40"
BUCKET="gs://news-discovery-webgraph"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

echo "Downloading CommonCrawl webgraph $VERSION..."

# Download new version
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-${VERSION}-*/domain/*-vertices.txt.gz
wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-${VERSION}-*/domain/*-edges.txt.gz

# Upload to GCS
echo "Uploading to GCS..."
gsutil -m cp *.txt.gz ${BUCKET}/${VERSION}/

# Update Cloud Run environment variable
echo "Updating Cloud Run..."
gcloud run services update discovery-worker \
  --region us-central1 \
  --update-env-vars WEBGRAPH_VERSION=${VERSION}

# Trigger redeploy (forces reload)
gcloud run services update discovery-worker \
  --region us-central1

echo "Update complete! New version: $VERSION"
echo "Old versions can be deleted from GCS to save costs."
```

**Run quarterly:**
```bash
./scripts/update-webgraph.sh 2025-40
```

### 10.2 Monitoring & Alerts

**Key Metrics to Monitor:**
1. **Cloud Run:**
   - Request latency (p50, p95, p99)
   - Error rate
   - Memory usage
   - CPU utilization

2. **Redis:**
   - Command count per day
   - Memory usage
   - Connection errors

3. **Application Metrics:**
   - Job completion rate
   - Average processing time
   - Failed job rate

**Set up Cloud Monitoring alerts:**
```bash
# Alert on high error rate
gcloud alpha monitoring policies create \
  --notification-channels="YOUR_CHANNEL_ID" \
  --display-name="High Error Rate" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-display-name="Error rate > 5%"
```

### 10.3 Backup & Recovery

**Data to Backup:**
- Webgraph files (already in GCS with versioning)
- Application code (in GitHub)
- Environment variables (documented in .env.example)

**Recovery Procedure:**
1. Redeploy Cloud Run from latest image
2. Restore environment variables
3. Verify webgraph data in GCS
4. Test with sample query

**RTO (Recovery Time Objective):** < 1 hour
**RPO (Recovery Point Objective):** 0 (stateless system)

---

## 11. Security Considerations

### 11.1 Authentication & Authorization

**Public Access:**
- Frontend: Public (no authentication required for MVP)
- Cloud Run Worker: Publicly accessible endpoint (unauthenticated)

**Rationale:** Low-risk academic tool with no sensitive data

**Future Enhancement:** Add simple API key or OAuth for rate limiting

### 11.2 Input Validation

**Frontend Validation:**
- Domain count: 1-1000
- Domain format: Basic regex check
- Threshold values: Numeric range validation

**Backend Validation:**
- Reject invalid domain names
- Limit processing time per job
- Validate job IDs from Redis

### 11.3 Rate Limiting

**Upstash Redis:**
- Use Redis for rate limiting (100 requests/hour per IP)
- Implement on Vercel API routes

**Implementation:**
```typescript
const rateLimitKey = `ratelimit:${ip}`
const count = await redis.incr(rateLimitKey)
if (count === 1) {
  await redis.expire(rateLimitKey, 3600)
}
if (count > 100) {
  return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429 })
}
```

### 11.4 Secret Management

**Never commit secrets to git:**
- Use `.env.local` for local development
- Store production secrets in GCP Secret Manager
- Reference secrets as environment variables in Cloud Run

**Secrets to Protect:**
- Upstash Redis credentials
- GCP service account keys
- Any future API keys

---

## 12. Testing Strategy

### 12.1 Frontend Testing

**Unit Tests (Jest + React Testing Library):**
```typescript
// DiscoveryForm.test.tsx
describe('DiscoveryForm', () => {
  it('validates minimum domain count', () => {
    // Submit empty form
    // Expect error message
  })
  
  it('submits job successfully', async () => {
    // Mock fetch
    // Fill form
    // Submit
    // Expect jobId returned
  })
  
  it('polls for results', async () => {
    // Mock polling responses
    // Verify result displayed after complete
  })
})
```

**E2E Tests (Playwright):**
```typescript
test('complete discovery flow', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await page.fill('textarea', 'example.com\ntest.org')
  await page.click('button[type="submit"]')
  await page.waitForSelector('table', { timeout: 60000 })
  expect(await page.locator('table tr').count()).toBeGreaterThan(0)
})
```

### 12.2 Backend Testing

**Unit Tests (JUnit):**
```java
@Test
public void testDiscoveryAlgorithm() {
    // Load sample graph
    // Run discovery with known seeds
    // Assert expected domains found
}

@Test
public void testThresholdFiltering() {
    // Test count-based threshold
    // Test percent-based threshold
}
```

**Integration Tests:**
```java
@Test
public void testEndToEnd() {
    // Submit job via HTTP
    // Wait for completion
    // Verify results in Redis
}
```

### 12.3 Performance Testing

**Load Test (k6):**
```javascript
import http from 'k6/http';

export default function() {
  const payload = JSON.stringify({
    domains: ['example.com', 'test.org'],
    minBacklinks: 5,
    direction: 'backlinks'
  });
  
  http.post('https://your-api.vercel.app/api/discover', payload, {
    headers: { 'Content-Type': 'application/json' }
  });
}

// Run: k6 run --vus 10 --duration 60s loadtest.js
```

**Targets:**
- Throughput: 100 requests/hour sustained
- Latency: p95 < 5 seconds for job submission
- Processing time: p95 < 10 minutes for 100 seed domains

---

## 13. Future Enhancements

### 13.1 Phase 2 Features

**Priority 1: User Accounts & History**
- Save past queries
- Bookmark discovered domains
- Share results via URL

**Priority 2: Advanced Filtering**
- Filter by domain TLD
- Exclude specific domains
- Set maximum results limit

**Priority 3: Batch Processing**
- Upload CSV of seed lists
- Process multiple queries at once
- Email notification on completion

**Priority 4: Visualization**
- Network graph of connections
- Heatmap of link density
- Time-series analysis (if multi-version webgraphs)

### 13.2 Scalability Improvements

**For >1000 queries/month:**
1. **Pre-compute adjacency lists:** Store in Redis or separate database
2. **Use Neo4j or TigerGraph:** For sub-second query times
3. **Add caching layer:** Cache popular seed list combinations
4. **Horizontal scaling:** Multiple Cloud Run instances

### 13.3 Research Extensions

**Integrate GNN Classifier:**
- Allow users to upload reliability labels
- Train GNN on-the-fly
- Predict reliability of discovered domains

**Multi-hop Discovery:**
- Discover domains 2+ hops away
- Identify link scheme clusters

**Temporal Analysis:**
- Compare webgraph versions over time
- Detect emerging link farms

---

## Appendix A: Repository Structure

```
news_source_discovery_webapp/
├── README.md                          # Project overview
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore rules
│
├── frontend/                          # Next.js application
│   ├── app/
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Landing page
│   │   ├── globals.css                # Global styles
│   │   └── api/
│   │       └── discover/
│   │           └── route.ts           # Discovery API route
│   ├── components/
│   │   └── DiscoveryForm.tsx          # Main form component
│   ├── lib/
│   │   └── redis.ts                   # Redis client
│   ├── public/                        # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── next.config.js
│   ├── .env.example
│   └── .env.local                     # Local env vars (gitignored)
│
├── backend/                           # Java worker
│   ├── src/
│   │   └── main/
│   │       ├── java/com/webgraph/discovery/
│   │       │   ├── Main.java          # Entry point
│   │       │   ├── DiscoveryWorker.java
│   │       │   ├── models/
│   │       │   │   ├── DiscoveryRequest.java
│   │       │   │   ├── DiscoveryResult.java
│   │       │   │   └── DiscoveredDomain.java
│   │       │   └── utils/
│   │       │       ├── RedisClient.java
│   │       │       └── GCSLoader.java
│   │       └── resources/
│   │           └── application.properties
│   ├── pom.xml                        # Maven dependencies
│   ├── Dockerfile                     # Container definition
│   ├── .dockerignore
│   └── deploy.sh                      # Deployment script
│
├── scripts/                           # Utility scripts
│   ├── update-webgraph.sh             # Quarterly update
│   ├── download-sample-graph.sh       # For local testing
│   └── setup-gcp.sh                   # Initial GCP setup
│
├── docs/                              # Documentation
│   ├── DEPLOYMENT.md                  # Deployment guide
│   ├── API.md                         # API documentation
│   ├── DEVELOPMENT.md                 # Dev environment setup
│   └── ARCHITECTURE.md                # Architecture diagrams
│
└── tests/                             # Test suites
    ├── e2e/                           # Playwright tests
    ├── load/                          # k6 load tests
    └── integration/                   # Integration tests
```

---

## Appendix B: Key Dependencies

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "@upstash/redis": "^1.28.4",
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "nanoid": "^5.0.4",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20.11.5",
    "@types/react": "^18.2.48",
    "typescript": "^5.3.3",
    "tailwindcss": "^3.4.1"
  }
}
```

### Backend (`pom.xml`)
```xml
<dependencies>
  <!-- Web Framework -->
  <dependency>
    <groupId>io.javalin</groupId>
    <artifactId>javalin</artifactId>
    <version>5.6.3</version>
  </dependency>
  
  <!-- WebGraph Framework -->
  <dependency>
    <groupId>it.unimi.dsi</groupId>
    <artifactId>webgraph</artifactId>
    <version>3.6.10</version>
  </dependency>
  
  <!-- Redis Client -->
  <dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
    <version>5.0.2</version>
  </dependency>
  
  <!-- JSON -->
  <dependency>
    <groupId>com.google.code.gson</groupId>
    <artifactId>gson</artifactId>
    <version>2.10.1</version>
  </dependency>
  
  <!-- GCS Client -->
  <dependency>
    <groupId>com.google.cloud</groupId>
    <artifactId>google-cloud-storage</artifactId>
    <version>2.32.1</version>
  </dependency>
  
  <!-- Logging -->
  <dependency>
    <groupId>org.slf4j</groupId>
    <artifactId>slf4j-simple</artifactId>
    <version>2.0.9</version>
  </dependency>
</dependencies>
```

---

## Appendix C: Environment Variables

### Frontend (`.env.local`)
```bash
# Upstash Redis
UPSTASH_REDIS_REST_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_token_here

# Cloud Run Worker
CLOUD_RUN_WORKER_URL=https://discovery-worker-xxxxx-uc.a.run.app
```

### Backend (Cloud Run env vars)
```bash
# Webgraph Configuration
GCS_BUCKET=news-discovery-webgraph
WEBGRAPH_VERSION=2025-26

# Redis (from Secret Manager)
UPSTASH_REDIS_URL=secret:upstash-url
UPSTASH_REDIS_TOKEN=secret:upstash-token

# Java Options
JAVA_TOOL_OPTIONS=-Xmx14g
```

---

## Appendix D: Reference Links

**Research Papers:**
- [Detection and Discovery of Misinformation Sources (ICWSM 2024)](https://arxiv.org/abs/2401.02379)
- [Misinformation Resilient Search Rankings (ACM TIST 2025)](https://dl.acm.org/doi/abs/10.1145/3702240)

**Code Repositories:**
- [Detection-and-Discovery-of-Misinformation-Sources](https://github.com/CASOS-IDeaS-CMU/Detection-and-Discovery-of-Misinformation-Sources)
- [cc-webgraph](https://github.com/commoncrawl/cc-webgraph)

**Data Sources:**
- [CommonCrawl Web Graphs](https://commoncrawl.org/web-graphs)
- [CommonCrawl Latest Release](https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2025-26-nov-dec-jan/index.html)

**Documentation:**
- [WebGraph Framework](https://webgraph.di.unimi.it/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Upstash Redis](https://docs.upstash.com/redis)

---

## Document Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-05 | Initial design specification | Claude |

---

**END OF SPECIFICATION DOCUMENT**
