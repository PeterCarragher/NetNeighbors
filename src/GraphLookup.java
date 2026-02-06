import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

import org.commoncrawl.webgraph.explore.Graph;

public final class GraphLookup {

    private GraphLookup() {}

    /* ======================
       IO
       ====================== */

    public static List<String> loadLabels(String path) throws Exception {
        return Files.readAllLines(Path.of(path)).stream()
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .toList();
    }

    /* ======================
       Label ↔ ID mapping
       ====================== */

    public static long[] labelsToIds(Graph g, List<String> labels) {
        return labels.stream()
            .map(g::vertexLabelToId)
            .filter(id -> id >= 0)
            .mapToLong(Long::longValue)
            .toArray();
    }

    public static List<String> idsToLabels(Graph g, long[] ids) {
        return Arrays.stream(ids)
            .mapToObj(g::vertexIdToLabel)
            .filter(Objects::nonNull)
            .toList();
    }

    /* ======================
       Graph queries
       ====================== */

    public static List<String> sharedPredecessorLabels(Graph g, long[] seedIds) {
        return idsToLabels(g, g.sharedPredecessors(seedIds));
    }

    public static List<String> sharedSuccessorLabels(Graph g, long[] seedIds) {
        return idsToLabels(g, g.sharedSuccessors(seedIds));
    }
}
