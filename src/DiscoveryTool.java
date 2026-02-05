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
        // For backlinks: use transpose graph (-t) where successors = predecessors
        // For outlinks: use regular graph where successors = outlinks
        String graphPath = direction.equals("backlinks") ? graphBase + "-t" : graphBase;

        System.out.println("=".repeat(60));
        System.out.println("Domain Discovery Tool");
        System.out.println("=".repeat(60));
        System.out.println("Direction: " + direction);
        System.out.println("Min connections: " + minConnections);
        System.out.println("Graph: " + graphPath);
        System.out.println();

        // Load the graph
        System.out.println("Loading graph...");
        long startTime = System.currentTimeMillis();
        BVGraph graph = BVGraph.load(graphPath);
        long loadTime = System.currentTimeMillis() - startTime;
        System.out.println("Graph loaded: " + String.format("%,d", graph.numNodes()) + " nodes");
        System.out.println("Load time: " + (loadTime / 1000.0) + " seconds");
        System.out.println();

        // Build domain <-> ID mappings
        System.out.println("Loading domain mappings...");
        startTime = System.currentTimeMillis();
        Map<String, Integer> domainToId = new HashMap<>();
        Map<Integer, String> idToDomain = new HashMap<>();

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

                    // Convert reversed domain (com.example) to normal (example.com)
                    String domain = reverseDomain(revDomain);

                    domainToId.put(domain, id);
                    idToDomain.put(id, domain);
                }
            }
        }
        loadTime = System.currentTimeMillis() - startTime;
        System.out.println("Loaded " + String.format("%,d", domainToId.size()) + " domain mappings");
        System.out.println("Load time: " + (loadTime / 1000.0) + " seconds");
        System.out.println();

        // Load seed domains
        System.out.println("Loading seed domains...");
        Set<Integer> seedIds = new HashSet<>();
        List<String> notFound = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(seedsFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                String domain = line.trim().toLowerCase();
                if (domain.isEmpty()) continue;

                Integer id = domainToId.get(domain);
                if (id != null) {
                    seedIds.add(id);
                } else {
                    notFound.add(domain);
                }
            }
        }

        System.out.println("Found " + seedIds.size() + " seed domains in graph");
        if (!notFound.isEmpty()) {
            System.out.println("Warning: " + notFound.size() + " domains not found in graph");
            if (notFound.size() <= 5) {
                for (String d : notFound) {
                    System.out.println("  - " + d);
                }
            } else {
                for (int i = 0; i < 5; i++) {
                    System.out.println("  - " + notFound.get(i));
                }
                System.out.println("  ... and " + (notFound.size() - 5) + " more");
            }
        }
        System.out.println();

        if (seedIds.isEmpty()) {
            System.err.println("Error: No valid seed domains found in graph!");
            System.exit(1);
        }

        // Run discovery
        System.out.println("Running discovery (" + direction + ")...");
        startTime = System.currentTimeMillis();
        Map<Integer, Integer> candidateCounts = new HashMap<>();

        int processed = 0;
        for (Integer seedId : seedIds) {
            // Get neighbors using successors()
            // In transpose graph: successors = who links TO this node (backlinks)
            // In regular graph: successors = who this node links TO (outlinks)
            LazyIntIterator neighbors = graph.successors(seedId);
            int neighbor;
            while ((neighbor = neighbors.nextInt()) != -1) {
                // Don't count seeds themselves
                if (!seedIds.contains(neighbor)) {
                    candidateCounts.merge(neighbor, 1, Integer::sum);
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
        System.out.println();

        // Filter by minimum connection threshold
        System.out.println("Filtering by threshold >= " + minConnections + "...");
        List<Map.Entry<Integer, Integer>> results = new ArrayList<>();
        for (Map.Entry<Integer, Integer> entry : candidateCounts.entrySet()) {
            if (entry.getValue() >= minConnections) {
                results.add(entry);
            }
        }

        // Sort by connection count descending
        results.sort((a, b) -> b.getValue() - a.getValue());
        System.out.println("Found " + String.format("%,d", results.size()) + " domains meeting threshold");
        System.out.println();

        // Write results to CSV
        System.out.println("Writing results to " + outputFile + "...");
        try (PrintWriter pw = new PrintWriter(new FileWriter(outputFile))) {
            pw.println("domain,connections,percentage");
            for (Map.Entry<Integer, Integer> entry : results) {
                String domain = idToDomain.get(entry.getKey());
                if (domain != null) {
                    int connections = entry.getValue();
                    double percentage = (connections * 100.0) / seedIds.size();
                    pw.printf("%s,%d,%.2f%n", domain, connections, percentage);
                }
            }
        }

        System.out.println();
        System.out.println("=".repeat(60));
        System.out.println("Discovery complete!");
        System.out.println("Results: " + String.format("%,d", results.size()) + " domains");
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
}
