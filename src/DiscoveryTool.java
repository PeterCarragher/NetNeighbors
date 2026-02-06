import it.unimi.dsi.webgraph.*;
import it.unimi.dsi.fastutil.ints.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;

/**
 * Domain discovery tool using CommonCrawl webgraph.
 *
 * Given a list of seed domains, discovers other domains that are connected
 * via backlinks or outlinks in the webgraph.
 *
 * Memory-optimized: Only loads domain mappings for seeds and results,
 * not the entire 100M+ domain list.
 *
 * Usage:
 *   java -cp "cc-webgraph.jar:." DiscoveryTool \
 *       --graph /path/to/graph-base \
 *       --vertices /path/to/vertices.txt.gz \
 *       --seeds /path/to/seeds.txt \
 *       --output /path/to/results.csv \
 *       --min-connections 5 \
 *       --direction backlinks
 */
public class DiscoveryTool {

    public static void main(String[] args) throws Exception {
        // Parse command line arguments
        String graphBase = null;
        String verticesFile = null;
        String seedsFile = null;
        String outputFile = null;
        int minConnections = 5;
        String direction = "backlinks";

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--graph":
                    graphBase = args[++i];
                    break;
                case "--vertices":
                    verticesFile = args[++i];
                    break;
                case "--seeds":
                    seedsFile = args[++i];
                    break;
                case "--output":
                    outputFile = args[++i];
                    break;
                case "--min-connections":
                    minConnections = Integer.parseInt(args[++i]);
                    break;
                case "--direction":
                    direction = args[++i].toLowerCase();
                    break;
                case "--help":
                    printUsage();
                    return;
            }
        }

        // Validate required arguments
        if (graphBase == null || verticesFile == null || seedsFile == null || outputFile == null) {
            System.err.println("Error: Missing required arguments");
            printUsage();
            System.exit(1);
        }

        if (!direction.equals("backlinks") && !direction.equals("outlinks")) {
            System.err.println("Error: Direction must be 'backlinks' or 'outlinks'");
            System.exit(1);
        }

        // Run discovery
        DiscoveryTool tool = new DiscoveryTool();
        tool.discover(graphBase, verticesFile, seedsFile, outputFile, minConnections, direction);
    }

    private static void printUsage() {
        System.out.println("Usage: java DiscoveryTool [options]");
        System.out.println();
        System.out.println("Required options:");
        System.out.println("  --graph <path>          Base path to graph files (without .graph extension)");
        System.out.println("  --vertices <path>       Path to vertices file (gzipped)");
        System.out.println("  --seeds <path>          Path to seeds file (one domain per line)");
        System.out.println("  --output <path>         Path to output CSV file");
        System.out.println();
        System.out.println("Optional:");
        System.out.println("  --min-connections <n>   Minimum connections threshold (default: 5)");
        System.out.println("  --direction <dir>       'backlinks' or 'outlinks' (default: backlinks)");
        System.out.println("  --help                  Show this help message");
    }

    public void discover(String graphBase, String verticesFile, String seedsFile,
                         String outputFile, int minConnections, String direction) throws Exception {

        // Determine which graph to load based on direction
        String graphPath = direction.equals("backlinks") ? graphBase + "-t" : graphBase;

        System.out.println("=".repeat(60));
        System.out.println("Domain Discovery Tool (Memory-Optimized)");
        System.out.println("=".repeat(60));
        System.out.println("Direction: " + direction);
        System.out.println("Min connections: " + minConnections);
        System.out.println("Graph: " + graphPath);
        System.out.println();

        // Load seed domains into a Set for fast lookup
        System.out.println("Loading seed domains...");
        Set<String> seedDomains = new HashSet<>();
        try (BufferedReader br = new BufferedReader(new FileReader(seedsFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                String domain = line.trim().toLowerCase();
                if (!domain.isEmpty()) {
                    seedDomains.add(domain);
                }
            }
        }
        System.out.println("Loaded " + seedDomains.size() + " seed domains");

        // PASS 1: Find IDs for seed domains only (memory efficient)
        System.out.println("\nMapping seed domains to graph IDs...");
        long startTime = System.currentTimeMillis();
        Int2ObjectOpenHashMap<String> seedIdToDomain = new Int2ObjectOpenHashMap<>();
        IntOpenHashSet seedIds = new IntOpenHashSet();
        int foundCount = 0;

        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(
                    new GZIPInputStream(
                        new FileInputStream(verticesFile))))) {
            String line;
            while ((line = br.readLine()) != null) {
                String[] parts = line.split("\t");
                if (parts.length >= 2) {
                    int id = Integer.parseInt(parts[0]);
                    String revDomain = parts[1];
                    String domain = reverseDomain(revDomain);

                    if (seedDomains.contains(domain)) {
                        seedIds.add(id);
                        seedIdToDomain.put(id, domain);
                        foundCount++;
                        if (foundCount == seedDomains.size()) {
                            break; // Found all seeds, stop scanning
                        }
                    }
                }
            }
        }

        long scanTime = System.currentTimeMillis() - startTime;
        System.out.println("Found " + seedIds.size() + "/" + seedDomains.size() + " seeds in graph");
        System.out.println("Scan time: " + (scanTime / 1000.0) + " seconds");

        if (seedIds.isEmpty()) {
            System.err.println("Error: No valid seed domains found in graph!");
            System.exit(1);
        }

        // Load the graph using memory-mapped I/O (minimal heap usage)
        System.out.println("\nLoading graph (memory-mapped)...");
        printMemoryUsage("Before graph load");
        startTime = System.currentTimeMillis();
        ImmutableGraph graph = ImmutableGraph.loadMapped(graphPath);
        long loadTime = System.currentTimeMillis() - startTime;
        System.out.println("Graph loaded: " + String.format("%,d", graph.numNodes()) + " nodes");
        System.out.println("Load time: " + (loadTime / 1000.0) + " seconds");
        printMemoryUsage("After graph load");

        // Run discovery
        System.out.println("\nRunning discovery (" + direction + ")...");
        startTime = System.currentTimeMillis();
        Int2IntOpenHashMap candidateCounts = new Int2IntOpenHashMap();
        candidateCounts.defaultReturnValue(0);

        int processed = 0;
        for (int seedId : seedIds) {
            LazyIntIterator neighbors = graph.successors(seedId);
            int neighbor;
            while ((neighbor = neighbors.nextInt()) != -1) {
                if (!seedIds.contains(neighbor)) {
                    candidateCounts.addTo(neighbor, 1);
                }
            }

            processed++;
            if (processed % 100 == 0 || processed == seedIds.size()) {
                System.out.print("\rProcessed " + processed + "/" + seedIds.size() + " seeds...");
            }
        }
        System.out.println();

        long discoveryTime = System.currentTimeMillis() - startTime;
        System.out.println("Found " + String.format("%,d", candidateCounts.size()) + " unique candidate domains");
        System.out.println("Discovery time: " + (discoveryTime / 1000.0) + " seconds");
        printMemoryUsage("After discovery");

        // Filter by minimum connection threshold
        System.out.println("\nFiltering by threshold >= " + minConnections + "...");
        IntArrayList resultIds = new IntArrayList();
        IntArrayList resultCounts = new IntArrayList();

        for (Int2IntMap.Entry entry : candidateCounts.int2IntEntrySet()) {
            if (entry.getIntValue() >= minConnections) {
                resultIds.add(entry.getIntKey());
                resultCounts.add(entry.getIntValue());
            }
        }

        System.out.println("Found " + String.format("%,d", resultIds.size()) + " domains meeting threshold");

        // Free memory before second pass
        candidateCounts = null;
        graph = null;
        System.gc();

        // PASS 2: Look up domain names only for results (memory efficient)
        System.out.println("\nLooking up result domain names...");
        startTime = System.currentTimeMillis();

        IntSet resultIdSet = new IntOpenHashSet(resultIds);
        Int2ObjectOpenHashMap<String> resultIdToDomain = new Int2ObjectOpenHashMap<>();

        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(
                    new GZIPInputStream(
                        new FileInputStream(verticesFile))))) {
            String line;
            while ((line = br.readLine()) != null) {
                String[] parts = line.split("\t");
                if (parts.length >= 2) {
                    int id = Integer.parseInt(parts[0]);
                    if (resultIdSet.contains(id)) {
                        String revDomain = parts[1];
                        String domain = reverseDomain(revDomain);
                        resultIdToDomain.put(id, domain);

                        if (resultIdToDomain.size() == resultIds.size()) {
                            break; // Found all results
                        }
                    }
                }
            }
        }

        scanTime = System.currentTimeMillis() - startTime;
        System.out.println("Lookup time: " + (scanTime / 1000.0) + " seconds");

        // Sort results by connection count descending
        Integer[] indices = new Integer[resultIds.size()];
        for (int i = 0; i < indices.length; i++) indices[i] = i;
        Arrays.sort(indices, (a, b) -> resultCounts.getInt(b) - resultCounts.getInt(a));

        // Write results to CSV
        System.out.println("\nWriting results to " + outputFile + "...");
        try (PrintWriter pw = new PrintWriter(new FileWriter(outputFile))) {
            pw.println("domain,connections,percentage");
            for (int idx : indices) {
                int id = resultIds.getInt(idx);
                int connections = resultCounts.getInt(idx);
                String domain = resultIdToDomain.get(id);
                if (domain != null) {
                    double percentage = (connections * 100.0) / seedIds.size();
                    pw.printf("%s,%d,%.2f%n", domain, connections, percentage);
                }
            }
        }

        System.out.println();
        System.out.println("=".repeat(60));
        System.out.println("Discovery complete!");
        System.out.println("Results: " + String.format("%,d", resultIds.size()) + " domains");
        System.out.println("Output: " + outputFile);
        System.out.println("=".repeat(60));
    }

    /**
     * Convert reversed domain notation (com.example.www) to normal (www.example.com)
     */
    private String reverseDomain(String revDomain) {
        String[] parts = revDomain.split("\\.");
        StringBuilder sb = new StringBuilder();
        for (int i = parts.length - 1; i >= 0; i--) {
            if (sb.length() > 0) sb.append(".");
            sb.append(parts[i]);
        }
        return sb.toString();
    }

    /**
     * Print current memory usage for diagnostics
     */
    private void printMemoryUsage(String label) {
        Runtime rt = Runtime.getRuntime();
        long used = (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024);
        long max = rt.maxMemory() / (1024 * 1024);
        System.out.println(String.format("[Memory] %s: %,d MB used / %,d MB max", label, used, max));
    }
}
