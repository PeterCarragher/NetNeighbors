package com.discovery;

import com.discovery.models.DiscoveredDomain;
import com.discovery.models.DiscoveryRequest;
import com.discovery.models.DiscoveryResult;
import org.commoncrawl.webgraph.explore.Graph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class DiscoveryService {
    private static final Logger LOG = LoggerFactory.getLogger(DiscoveryService.class);

    private Graph graph;
    private boolean graphLoaded = false;

    public DiscoveryService() {}

    public void loadGraph(String graphPath) throws Exception {
        LOG.info("Loading graph from: {}", graphPath);
        long start = System.currentTimeMillis();
        graph = new Graph(graphPath);
        graphLoaded = true;
        LOG.info("Graph loaded in {}ms", System.currentTimeMillis() - start);
    }

    public boolean isGraphLoaded() {
        return graphLoaded;
    }

    public DiscoveryResult discover(DiscoveryRequest request) {
        DiscoveryResult result = new DiscoveryResult();
        result.setDomain(request.getDomain());
        result.setDirection(request.getDirection());
        result.setThreshold(request.getThreshold());

        if (!graphLoaded) {
            result.setStatus("error");
            result.setError("Graph not loaded");
            return result;
        }

        long startTime = System.currentTimeMillis();

        try {
            // Convert domain to reverse notation (e.g., "example.com" -> "com.example")
            String reversedDomain = reverseDomainName(request.getDomain().toLowerCase().trim());
            LOG.info("Looking up domain: {} (reversed: {})", request.getDomain(), reversedDomain);

            // Check if domain exists in graph
            long vertexId = graph.vertexLabelToId(reversedDomain);
            if (vertexId == -1) {
                result.setStatus("error");
                result.setError("Domain not found in webgraph: " + request.getDomain());
                return result;
            }

            // Get neighbors based on direction
            Stream<String> neighborStream;
            if ("incoming".equalsIgnoreCase(request.getDirection())) {
                // Domains that link TO this domain (predecessors)
                neighborStream = graph.predecessorStream(reversedDomain);
            } else {
                // Domains that this domain links TO (successors)
                neighborStream = graph.successorStream(reversedDomain);
            }

            // Aggregate by registered domain and count
            Map<String, Long> domainCounts = neighborStream
                .map(this::getRegisteredDomain)
                .filter(Objects::nonNull)
                .collect(Collectors.groupingBy(d -> d, Collectors.counting()));

            // Filter by threshold and sort by count descending
            List<DiscoveredDomain> discovered = domainCounts.entrySet().stream()
                .filter(e -> e.getValue() >= request.getThreshold())
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .map(e -> new DiscoveredDomain(unreverseDomainName(e.getKey()), e.getValue()))
                .collect(Collectors.toList());

            result.setResults(discovered);
            result.setTotalFound(discovered.size());
            result.setStatus("completed");
            result.setProcessingTimeMs(System.currentTimeMillis() - startTime);

            LOG.info("Discovery completed for {}: found {} domains above threshold {} in {}ms",
                request.getDomain(), discovered.size(), request.getThreshold(), result.getProcessingTimeMs());

        } catch (Exception e) {
            LOG.error("Error during discovery for domain: {}", request.getDomain(), e);
            result.setStatus("error");
            result.setError("Discovery failed: " + e.getMessage());
        }

        return result;
    }

    /**
     * Reverse a domain name: "www.example.com" -> "com.example.www"
     */
    private String reverseDomainName(String domain) {
        // Remove protocol if present
        domain = domain.replaceFirst("^https?://", "");
        // Remove path if present
        int slashIdx = domain.indexOf('/');
        if (slashIdx > 0) {
            domain = domain.substring(0, slashIdx);
        }
        // Remove port if present
        int colonIdx = domain.indexOf(':');
        if (colonIdx > 0) {
            domain = domain.substring(0, colonIdx);
        }

        String[] parts = domain.split("\\.");
        StringBuilder reversed = new StringBuilder();
        for (int i = parts.length - 1; i >= 0; i--) {
            if (reversed.length() > 0) {
                reversed.append(".");
            }
            reversed.append(parts[i]);
        }
        return reversed.toString();
    }

    /**
     * Unreverse a domain name: "com.example.www" -> "www.example.com"
     */
    private String unreverseDomainName(String reversed) {
        String[] parts = reversed.split("\\.");
        StringBuilder unreversed = new StringBuilder();
        for (int i = parts.length - 1; i >= 0; i--) {
            if (unreversed.length() > 0) {
                unreversed.append(".");
            }
            unreversed.append(parts[i]);
        }
        return unreversed.toString();
    }

    /**
     * Get the registered domain from a reversed host name.
     * For "com.example.www" returns "com.example"
     */
    private String getRegisteredDomain(String reversedHost) {
        try {
            return Graph.getRegisteredDomainReversed(reversedHost, false);
        } catch (Exception e) {
            // Fallback: just return first two parts for simple TLDs
            String[] parts = reversedHost.split("\\.");
            if (parts.length >= 2) {
                return parts[0] + "." + parts[1];
            }
            return reversedHost;
        }
    }
}
