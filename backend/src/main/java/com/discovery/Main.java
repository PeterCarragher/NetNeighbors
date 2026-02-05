package com.discovery;

import com.discovery.models.DiscoveryRequest;
import com.discovery.models.DiscoveryResult;
import com.google.gson.Gson;
import io.javalin.Javalin;
import io.javalin.http.Context;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import redis.clients.jedis.JedisPooled;

import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class Main {
    private static final Logger LOG = LoggerFactory.getLogger(Main.class);
    private static final Gson gson = new Gson();
    private static final int RESULT_TTL_SECONDS = 3600; // 1 hour

    private static DiscoveryService discoveryService;
    private static JedisPooled redis;
    private static ExecutorService executor;

    public static void main(String[] args) {
        // Get configuration from environment
        String graphPath = System.getenv("GRAPH_PATH");
        String redisUrl = System.getenv("UPSTASH_REDIS_REST_URL");
        String redisToken = System.getenv("UPSTASH_REDIS_REST_TOKEN");
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));

        if (graphPath == null || graphPath.isEmpty()) {
            LOG.error("GRAPH_PATH environment variable is required");
            System.exit(1);
        }

        // Initialize services
        discoveryService = new DiscoveryService();
        executor = Executors.newFixedThreadPool(4);

        // Initialize Redis if configured
        if (redisUrl != null && !redisUrl.isEmpty()) {
            try {
                // Parse Upstash Redis URL (format: https://xxx.upstash.io)
                // Convert to redis:// format for Jedis
                String jedisUrl = redisUrl.replace("https://", "rediss://default:" + redisToken + "@");
                redis = new JedisPooled(java.net.URI.create(jedisUrl));
                LOG.info("Connected to Redis");
            } catch (Exception e) {
                LOG.warn("Failed to connect to Redis, running without caching: {}", e.getMessage());
            }
        } else {
            LOG.info("Redis not configured, running without caching");
        }

        // Load graph asynchronously
        executor.submit(() -> {
            try {
                discoveryService.loadGraph(graphPath);
            } catch (Exception e) {
                LOG.error("Failed to load graph", e);
            }
        });

        // Create Javalin app
        Javalin app = Javalin.create(config -> {
            config.http.defaultContentType = "application/json";
        });

        // CORS handling
        app.before(ctx -> {
            ctx.header("Access-Control-Allow-Origin", "*");
            ctx.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            ctx.header("Access-Control-Allow-Headers", "Content-Type");
        });

        app.options("/*", ctx -> ctx.status(200));

        // Health endpoint
        app.get("/health", ctx -> {
            if (discoveryService.isGraphLoaded()) {
                ctx.result("{\"status\":\"ok\",\"graph\":\"loaded\"}");
            } else {
                ctx.result("{\"status\":\"ok\",\"graph\":\"loading\"}");
            }
        });

        // Discovery endpoint
        app.post("/discover", Main::handleDiscover);

        // Get result endpoint
        app.get("/result/{jobId}", Main::handleGetResult);

        // Start server
        app.start(port);
        LOG.info("Server started on port {}", port);
    }

    private static void handleDiscover(Context ctx) {
        try {
            DiscoveryRequest request = gson.fromJson(ctx.body(), DiscoveryRequest.class);

            // Validate request
            if (request.getDomain() == null || request.getDomain().isEmpty()) {
                ctx.status(400).result("{\"error\":\"domain is required\"}");
                return;
            }
            if (request.getThreshold() <= 0) {
                request.setThreshold(1);
            }
            if (request.getDirection() == null || request.getDirection().isEmpty()) {
                request.setDirection("outgoing");
            }

            // Generate job ID
            String jobId = UUID.randomUUID().toString();

            // Check if graph is loaded
            if (!discoveryService.isGraphLoaded()) {
                ctx.status(503).result("{\"error\":\"Graph is still loading, please try again later\"}");
                return;
            }

            // For small/fast queries, process synchronously
            // For large queries, could use async processing with Redis
            DiscoveryResult result = discoveryService.discover(request);
            result.setJobId(jobId);

            // Store in Redis if available
            if (redis != null) {
                try {
                    redis.setex("job:" + jobId, RESULT_TTL_SECONDS, gson.toJson(result));
                } catch (Exception e) {
                    LOG.warn("Failed to cache result in Redis: {}", e.getMessage());
                }
            }

            ctx.result(gson.toJson(result));
        } catch (Exception e) {
            LOG.error("Error handling discover request", e);
            ctx.status(500).result("{\"error\":\"Internal server error: " + e.getMessage() + "\"}");
        }
    }

    private static void handleGetResult(Context ctx) {
        String jobId = ctx.pathParam("jobId");

        if (redis == null) {
            ctx.status(404).result("{\"error\":\"Result not found (caching disabled)\"}");
            return;
        }

        try {
            String resultJson = redis.get("job:" + jobId);
            if (resultJson == null) {
                ctx.status(404).result("{\"error\":\"Result not found or expired\"}");
                return;
            }
            ctx.result(resultJson);
        } catch (Exception e) {
            LOG.error("Error retrieving result", e);
            ctx.status(500).result("{\"error\":\"Failed to retrieve result\"}");
        }
    }
}
