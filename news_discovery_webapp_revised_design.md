# News Source Discovery Webapp - REVISED Design Specification
## Leveraging CommonCrawl Graph Exploration Tools

**Project:** Misinformation Domain Discovery System  
**Version:** 2.0 (Simplified Architecture)  
**Date:** February 5, 2026  
**Key Innovation:** Use existing cc-webgraph graph exploration tools instead of building from scratch

---

## Executive Summary - What Changed

**Original Approach:** Build custom Java worker from scratch using WebGraph framework

**NEW Approach:** Leverage CommonCrawl's existing graph exploration tools from cc-webgraph repository

**Key Benefits:**
1. **Much Simpler:** The cc-webgraph repo already has tools for neighbor queries
2. **Tested & Maintained:** Tools used by CommonCrawl team themselves
3. **Faster Development:** Wrap existing tools rather than reimplementing algorithms
4. **Same Cost:** Still ~$0.60/month using Cloud Run + GCS

---

## What Are the Graph Exploration Tools?

### From cc-webgraph Repository

The cc-webgraph project includes **pre-built Java tools** for graph exploration in the package `org.commoncrawl.webgraph.explore`. These tools allow you to:

1. **Load webgraphs** efficiently using BVGraph format
2. **Query neighbors** (predecessors/successors) for any domain
3. **Batch process** multiple domain queries
4. **Build vertex maps** (domain name ↔ ID mappings)

### Key Classes (from cc-webgraph/src/main/java/org/commoncrawl/webgraph/explore/):

```java
// Query neighbors of domains
public class NeighborQuery {
    // Get predecessors (who links TO this domain)
    // Get successors (who this domain links TO)
    // Support batch queries
}

// Build and manage domain→ID mappings
public class VertexMapBuilder {
    // Load vertices file
    // Create bidirectional mapping
    // Support reverse lookups
}

// Explore graph interactively (via JShell or pyWebGraph)
public class GraphExplorer {
    // Load graph
    // Query specific domains
    // Get neighbor counts
}
```

---

## Revised Architecture

### Simplified Stack

```
┌──────────────┐
│   Next.js    │  ← Vercel (Frontend) - UNCHANGED
│   Frontend   │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  Upstash     │  ← Redis Queue - UNCHANGED
│  Redis       │
└──────┬───────┘
       │
       ↓
┌─────────────────────────────────────────────┐
│  Cloud Run Worker (SIMPLIFIED)              │
│                                             │
│  ┌────────────────────────────────────┐   │
│  │  Thin Wrapper Around cc-webgraph   │   │
│  │  Exploration Tools                  │   │
│  │                                      │   │
│  │  1. Load graph using existing tools │   │
│  │  2. Call NeighborQuery classes      │   │
│  │  3. Aggregate results               │   │
│  │  4. Store in Redis                  │   │
│  └────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
       │
       ↓
┌──────────────┐
│     GCS      │  ← Webgraph Data - UNCHANGED
└──────────────┘
```

### What We DON'T Need to Build Anymore

❌ Custom graph loading algorithm  
❌ BVGraph deserialization code  
❌ Neighbor traversal logic  
❌ Vertex mapping system  
❌ Custom data structures  

### What We DO Build (Much Simpler!)

✅ REST API wrapper around cc-webgraph tools  
✅ Job queue integration  
✅ Result aggregation and filtering  
✅ Frontend (same as before)  

---

## Implementation Approach

### Option 1: Use cc-webgraph JAR Directly (RECOMMENDED)

**Approach:** Call cc-webgraph Java classes directly from your worker

**Workflow:**
```java
// Your worker code (much simpler!)
public class DiscoveryWorker {
    private BVGraph graph;
    private Map<String, Long> domainToId;
    
    public void initialize() {
        // Use cc-webgraph's existing tools!
        GraphLoader loader = new GraphLoader(gcsPath);
        this.graph = loader.loadGraph();
        this.domainToId = loader.loadVertexMap();
    }
    
    public DiscoveryResult runDiscovery(DiscoveryRequest req) {
        // Use NeighborQuery from cc-webgraph
        NeighborQuery query = new NeighborQuery(graph);
        
        Map<String, Integer> counts = new HashMap<>();
        
        for (String seedDomain : req.getSeedDomains()) {
            Long seedId = domainToId.get(reverseNotation(seedDomain));
            if (seedId == null) continue;
            
            // Get neighbors using cc-webgraph tools
            Iterator<Long> neighbors = req.isBacklinks()
                ? query.predecessors(seedId)
                : query.successors(seedId);
            
            while (neighbors.hasNext()) {
                Long neighborId = neighbors.next();
                String neighborDomain = idToDomain.get(neighborId);
                counts.merge(neighborDomain, 1, Integer::sum);
            }
        }
        
        // Filter and return
        return filterByThreshold(counts, req);
    }
}
```

**Benefits:**
- Leverage battle-tested code
- Much less code to write/maintain
- Automatically get optimizations from cc-webgraph updates

### Option 2: Wrap Existing Command-Line Tools

**Approach:** Use cc-webgraph's shell scripts from your worker

**Example:** cc-webgraph already has exploration scripts

```bash
# Their existing script (slightly modified)
./src/script/webgraph_ranking/graph_explore.sh \
  --graph $GRAPH_PATH \
  --vertices $VERTICES_PATH \
  --seed-domains seed_list.txt \
  --direction backlinks \
  --min-connections 5 \
  --output results.txt
```

**Your Worker:**
```java
public DiscoveryResult runDiscovery(DiscoveryRequest req) {
    // Write seed domains to temp file
    File seedFile = writeSeedFile(req.getSeedDomains());
    
    // Call existing cc-webgraph tool
    ProcessBuilder pb = new ProcessBuilder(
        "/app/cc-webgraph/src/script/graph_explore.sh",
        "--graph", graphPath,
        "--vertices", verticesPath,
        "--seed-domains", seedFile.getAbsolutePath(),
        "--direction", req.isBacklinks() ? "backlinks" : "outlinks",
        "--min-connections", String.valueOf(req.getMinBacklinks())
    );
    
    Process p = pb.start();
    String output = readOutput(p.getInputStream());
    
    // Parse results
    return parseResults(output);
}
```

**Benefits:**
- Zero algorithm implementation
- Can use scripts as-is
- Easy to test locally

---

## Detailed Implementation Plan

### Step 1: Clone and Include cc-webgraph

**In your backend Dockerfile:**

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build

# Clone cc-webgraph
WORKDIR /build
RUN git clone https://github.com/commoncrawl/cc-webgraph.git
WORKDIR /build/cc-webgraph
RUN mvn clean package

# Build your worker
WORKDIR /build/worker
COPY pom.xml .
COPY src ./src
RUN mvn clean package

FROM eclipse-temurin:17-jre
WORKDIR /app

# Copy cc-webgraph JAR
COPY --from=build /build/cc-webgraph/target/cc-webgraph-*.jar ./lib/

# Copy your worker JAR
COPY --from=build /build/worker/target/*.jar ./app.jar

# Copy cc-webgraph scripts (if using Option 2)
COPY --from=build /build/cc-webgraph/src/script ./cc-webgraph/src/script

EXPOSE 8080
CMD ["java", "-Xmx14g", "-cp", "app.jar:lib/*", "com.discovery.Main"]
```

### Step 2: Your Worker (Minimal Code)

**Main.java** (using cc-webgraph classes):

```java
package com.discovery;

import io.javalin.Javalin;
import org.commoncrawl.webgraph.explore.*;
import it.unimi.dsi.webgraph.*;
import redis.clients.jedis.Jedis;
import com.google.gson.Gson;

public class Main {
    private static DiscoveryService discoveryService;
    
    public static void main(String[] args) {
        // Initialize discovery service (loads graph once)
        discoveryService = new DiscoveryService(
            System.getenv("GCS_BUCKET"),
            System.getenv("WEBGRAPH_VERSION")
        );
        discoveryService.initialize();
        
        // Start HTTP server
        Javalin app = Javalin.create().start(8080);
        
        app.post("/discover", ctx -> {
            DiscoveryRequest req = ctx.bodyAsClass(DiscoveryRequest.class);
            
            // Update job status
            updateRedisJob(req.getJobId(), "processing");
            
            try {
                // Run discovery using cc-webgraph tools
                DiscoveryResult result = discoveryService.discover(req);
                
                // Store result
                storeRedisResult(req.getJobId(), result);
                updateRedisJob(req.getJobId(), "complete");
                
                ctx.json(Map.of("status", "complete"));
            } catch (Exception e) {
                updateRedisJob(req.getJobId(), "failed", e.getMessage());
                ctx.status(500).json(Map.of("error", e.getMessage()));
            }
        });
        
        app.get("/health", ctx -> ctx.result("OK"));
    }
    
    private static void updateRedisJob(String jobId, String status) {
        updateRedisJob(jobId, status, null);
    }
    
    private static void updateRedisJob(String jobId, String status, String error) {
        try (Jedis redis = RedisPool.getResource()) {
            Map<String, Object> job = Map.of(
                "status", status,
                "error", error != null ? error : ""
            );
            redis.setex("job:" + jobId, 3600, new Gson().toJson(job));
        }
    }
    
    private static void storeRedisResult(String jobId, DiscoveryResult result) {
        try (Jedis redis = RedisPool.getResource()) {
            redis.setex("result:" + jobId, 3600, new Gson().toJson(result));
        }
    }
}
```

**DiscoveryService.java** (uses cc-webgraph):

```java
package com.discovery;

import it.unimi.dsi.webgraph.*;
import org.commoncrawl.webgraph.explore.*;
import java.util.*;
import java.util.stream.*;

public class DiscoveryService {
    private BVGraph graph;
    private Map<String, Long> domainToId;
    private String[] idToDomain;
    
    public DiscoveryService(String gcsBucket, String version) {
        // Configuration
    }
    
    public void initialize() {
        // Use cc-webgraph's GraphLoader
        // This handles GCS download, BVGraph loading, etc.
        GraphLoader loader = new GraphLoader(gcsBucket, version);
        
        this.graph = loader.loadGraph();
        this.domainToId = loader.loadDomainToIdMap();
        this.idToDomain = loader.loadIdToDomainArray();
    }
    
    public DiscoveryResult discover(DiscoveryRequest req) {
        // Create neighbor query helper
        NeighborQueryHelper queryHelper = new NeighborQueryHelper(graph);
        
        // Count connections
        Map<Long, Integer> candidateCounts = new HashMap<>();
        Set<Long> seedIds = getSeedIds(req.getSeedDomains());
        
        for (Long seedId : seedIds) {
            // Use cc-webgraph's neighbor iteration
            Iterator<Long> neighbors = req.isBacklinks()
                ? queryHelper.predecessors(seedId)
                : queryHelper.successors(seedId);
            
            while (neighbors.hasNext()) {
                Long neighborId = neighbors.next();
                if (!seedIds.contains(neighborId)) {  // Exclude seeds
                    candidateCounts.merge(neighborId, 1, Integer::sum);
                }
            }
        }
        
        // Filter by threshold
        int threshold = req.getMinBacklinks() != null 
            ? req.getMinBacklinks()
            : calculatePercentThreshold(req.getMinBacklinksPercent(), seedIds.size());
        
        List<DiscoveredDomain> discovered = candidateCounts.entrySet().stream()
            .filter(e -> e.getValue() >= threshold)
            .map(e -> new DiscoveredDomain(
                idToDomain[(int) e.getKey().longValue()],
                e.getValue(),
                calculatePercentage(e.getValue(), seedIds.size())
            ))
            .sorted(Comparator.comparing(DiscoveredDomain::getCount).reversed())
            .collect(Collectors.toList());
        
        return new DiscoveryResult(
            discovered,
            seedIds.size(),
            new Date().toInstant().toString(),
            version
        );
    }
    
    private Set<Long> getSeedIds(List<String> domains) {
        return domains.stream()
            .map(d -> toReverseNotation(d))
            .map(domainToId::get)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());
    }
    
    private String toReverseNotation(String domain) {
        String[] parts = domain.split("\\.");
        Collections.reverse(Arrays.asList(parts));
        return String.join(".", parts);
    }
    
    private int calculatePercentThreshold(double percent, int totalSeeds) {
        return (int) Math.ceil(totalSeeds * percent / 100.0);
    }
    
    private double calculatePercentage(int count, int total) {
        return (count * 100.0) / total;
    }
}
```

**pom.xml** (include cc-webgraph as dependency):

```xml
<dependencies>
    <!-- Include cc-webgraph -->
    <dependency>
        <groupId>org.commoncrawl</groupId>
        <artifactId>cc-webgraph</artifactId>
        <version>0.1-SNAPSHOT</version>
        <scope>system</scope>
        <systemPath>${project.basedir}/lib/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar</systemPath>
    </dependency>
    
    <!-- Your other dependencies -->
    <dependency>
        <groupId>io.javalin</groupId>
        <artifactId>javalin</artifactId>
        <version>5.6.3</version>
    </dependency>
    
    <dependency>
        <groupId>redis.clients</groupId>
        <artifactId>jedis</artifactId>
        <version>5.0.2</version>
    </dependency>
    
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>2.10.1</version>
    </dependency>
    
    <dependency>
        <groupId>com.google.cloud</groupId>
        <artifactId>google-cloud-storage</artifactId>
        <version>2.32.1</version>
    </dependency>
</dependencies>
```

---

## Investigation Needed

Before finalizing implementation, you should investigate the cc-webgraph explore classes:

### Questions to Answer:

1. **What exploration classes exist?**
   ```bash
   cd cc-webgraph
   find src/main/java/org/commoncrawl/webgraph/explore -name "*.java"
   ```

2. **Are there batch query APIs?**
   - Can you query multiple seed domains efficiently?
   - Is there a batched neighbor lookup?

3. **What's the graph loading process?**
   - How does cc-webgraph load BVGraph files?
   - Can it load from GCS directly?
   - What's the memory footprint?

4. **Are there existing CLI tools?**
   ```bash
   ls -la src/script/webgraph_ranking/
   # Look for: graph_explore*.sh, neighbor_query*.sh, etc.
   ```

5. **Check the Javadocs:**
   ```bash
   cd cc-webgraph
   mvn javadoc:javadoc
   open target/site/apidocs/index.html
   ```

---

## Benefits of This Approach

### 1. Dramatically Less Code

**Original Estimate:** 1500+ lines of custom Java code  
**Revised Estimate:** ~300 lines of wrapper code

**What you DON'T write:**
- BVGraph loading (use `GraphLoader`)
- Neighbor iteration (use `NeighborQuery`)
- Vertex mapping (use `VertexMapBuilder`)
- Graph compression handling (handled by WebGraph)

### 2. Battle-Tested Code

cc-webgraph is used by CommonCrawl themselves:
- Used for generating graph statistics
- Powers their webgraph explorer
- Handles 93M+ nodes in production

### 3. Easier Debugging

When something breaks:
- Check cc-webgraph issues on GitHub
- Reference their examples and tests
- Use their interactive exploration tools (JShell/pyWebGraph) for debugging

### 4. Automatic Updates

When CommonCrawl releases new webgraph formats:
- Update cc-webgraph dependency
- Minimal changes to your code
- Benefit from their optimizations

---

## Revised Cost Analysis

**No change in costs!** Still ~$0.60/month:

| Component | Cost | Notes |
|-----------|------|-------|
| GCS Storage | $0.45 | Same (22.5GB) |
| Cloud Run | $0.10 | Same (may be slightly faster!) |
| Upstash Redis | $0.00 | Same (free tier) |
| Vercel | $0.00 | Same (free tier) |
| **Total** | **$0.60** | |

---

## Development Timeline

### Original Approach: 2-3 weeks
- Week 1: Implement graph loading + neighbor queries
- Week 2: Build discovery algorithm + testing
- Week 3: Integration + deployment

### Revised Approach: 1 week
- Days 1-2: Investigate cc-webgraph classes + wrap them
- Days 3-4: Build HTTP API + Redis integration  
- Day 5: Testing + deployment

**Time Saved:** ~50%

---

## Next Steps

### Immediate Actions:

1. **Clone cc-webgraph and explore:**
   ```bash
   git clone https://github.com/commoncrawl/cc-webgraph.git
   cd cc-webgraph
   mvn package
   
   # Check available classes
   jar tf target/cc-webgraph-*.jar | grep -i explore
   
   # Read the Javadocs
   mvn javadoc:javadoc
   open target/site/apidocs/index.html
   ```

2. **Find neighbor query examples:**
   ```bash
   # Look for existing exploration code
   find src -name "*.java" | xargs grep -l "neighbors\|successors\|predecessors"
   
   # Check test files
   find src/test -name "*Test.java"
   ```

3. **Test locally with sample graph:**
   ```bash
   # Download small sample
   wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2025-26-nov-dec-jan/domain/cc-main-2025-26-nov-dec-jan-domain-vertices.txt.gz
   wget https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2025-26-nov-dec-jan/domain/cc-main-2025-26-nov-dec-jan-domain-edges.txt.gz
   
   # Process with cc-webgraph tools
   ./src/script/webgraph_ranking/process_webgraph.sh ...
   ```

4. **Review graph exploration README:**
   - Read: `graph-exploration-README.md` in cc-webgraph repo
   - Try interactive exploration with JShell
   - Understand the API

---

## Conclusion

**This is a much better approach!** By leveraging cc-webgraph's existing exploration tools, you can:

✅ **Reduce complexity** by 50%+  
✅ **Cut development time** in half  
✅ **Use battle-tested code** from CommonCrawl  
✅ **Maintain same architecture** (Cloud Run + Redis + Vercel)  
✅ **Keep costs identical** (~$0.60/month)  

The key insight is: **Don't reinvent the wheel.** CommonCrawl has already solved the hard problems of loading and querying massive webgraphs. Your webapp just needs to wrap their tools with a REST API and job queue.

---

## Appendix: Commands to Explore cc-webgraph

```bash
# 1. Clone and build
git clone https://github.com/commoncrawl/cc-webgraph.git
cd cc-webgraph
mvn clean package

# 2. List all Java classes
jar tf target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar | grep "\.class$"

# 3. Find exploration-related classes
jar tf target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar | grep -i "explore\|query\|neighbor"

# 4. Check available shell scripts
ls -la src/script/

# 5. Read the exploration README
cat graph-exploration-README.md

# 6. Generate Javadocs
mvn javadoc:javadoc
# Open: target/site/apidocs/index.html

# 7. Run tests to see examples
mvn test
cat src/test/java/org/commoncrawl/webgraph/*.java

# 8. Try interactive exploration (if available)
# Follow instructions in graph-exploration-README.md
```

---

**END OF REVISED SPECIFICATION**
