import React, { useRef, useEffect, useCallback, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

/**
 * ForceGraph - A Dash component wrapping force-graph-2d for high-performance
 * graph visualization with WebGL rendering.
 */
const ForceGraph = (props) => {
    const {
        id,
        nodes,
        links,
        selectedNodes,
        width,
        height,
        nodeColor,
        linkColor,
        linkWidth,
        enableZoom,
        enablePan,
        enableNodeDrag,
        cooldownTicks,
        centerAt,
        zoomLevel,
        setProps,
    } = props;

    const graphRef = useRef();
    const containerRef = useRef();
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [selectedSet, setSelectedSet] = useState(new Set(selectedNodes || []));
    const [dimensions, setDimensions] = useState({ width: width || 800, height: height || 600 });

    // Update dimensions from props or container
    useEffect(() => {
        if (width && height) {
            setDimensions({ width, height });
        } else if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                setDimensions({ width: rect.width, height: rect.height });
            }
        }
    }, [width, height]);

    // Update graph data when nodes/links change
    useEffect(() => {
        // Create copies with mutable properties for force-graph
        const nodesCopy = (nodes || []).map(n => ({ ...n }));
        const linksCopy = (links || []).map(l => ({ ...l }));
        setGraphData({ nodes: nodesCopy, links: linksCopy });
    }, [nodes, links]);

    // Sync selection from props
    useEffect(() => {
        setSelectedSet(new Set(selectedNodes || []));
    }, [selectedNodes]);

    // Center on node when centerAt changes
    useEffect(() => {
        if (centerAt && graphRef.current) {
            const node = graphData.nodes.find(n => n.id === centerAt);
            if (node && node.x !== undefined) {
                graphRef.current.centerAt(node.x, node.y, 500);
                graphRef.current.zoom(2, 500);
            }
        }
    }, [centerAt, graphData.nodes]);

    // Apply zoom level
    useEffect(() => {
        if (zoomLevel && graphRef.current) {
            graphRef.current.zoom(zoomLevel, 300);
        }
    }, [zoomLevel]);

    // Node click handler - defensive about event being undefined
    const handleNodeClick = useCallback((node, event) => {
        if (!node) return;

        const ctrlKey = event?.ctrlKey || false;
        const metaKey = event?.metaKey || false;
        const shiftKey = event?.shiftKey || false;

        let newSelected;
        if (ctrlKey || metaKey) {
            // Multi-select with Ctrl/Cmd
            const newSet = new Set(selectedSet);
            if (newSet.has(node.id)) {
                newSet.delete(node.id);
            } else {
                newSet.add(node.id);
            }
            newSelected = Array.from(newSet);
        } else if (shiftKey) {
            // Add to selection with Shift
            const newSet = new Set(selectedSet);
            newSet.add(node.id);
            newSelected = Array.from(newSet);
        } else {
            // Single select
            newSelected = [node.id];
        }

        setSelectedSet(new Set(newSelected));
        if (setProps) {
            setProps({ selectedNodes: newSelected });
        }
    }, [selectedSet, setProps]);

    // Background click - clear selection
    const handleBackgroundClick = useCallback((event) => {
        setSelectedSet(new Set());
        if (setProps) {
            setProps({ selectedNodes: [] });
        }
    }, [setProps]);

    // Right-click handler for context menu
    const handleNodeRightClick = useCallback((node, event) => {
        if (!node) return;
        if (event?.preventDefault) {
            event.preventDefault();
        }
        if (setProps) {
            setProps({
                rightClickedNode: node.id,
                rightClickPosition: {
                    x: event?.clientX || 0,
                    y: event?.clientY || 0
                }
            });
        }
    }, [setProps]);

    // Node color function - highlight selected nodes
    const getNodeColor = useCallback((node) => {
        if (selectedSet.has(node.id)) {
            return '#ffd93d'; // Selected color
        }
        if (node.color) {
            return node.color;
        }
        // Default colors based on node type
        if (node.type === 'seed' || node.type === 'casino' || node.type === 'misinfo') {
            return '#ff6b6b';
        }
        return '#4ecdc4';
    }, [selectedSet]);

    // Node size function
    const getNodeSize = useCallback((node) => {
        const baseSize = node.connections ? Math.sqrt(node.connections) + 3 : 5;
        if (selectedSet.has(node.id)) {
            return baseSize * 1.3; // Larger when selected
        }
        return baseSize;
    }, [selectedSet]);

    // Link color - highlight links connected to selected nodes
    const getLinkColor = useCallback((link) => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;

        if (selectedSet.has(sourceId) || selectedSet.has(targetId)) {
            return 'rgba(255, 217, 61, 0.8)'; // Highlight color
        }
        return linkColor || 'rgba(150, 150, 150, 0.3)';
    }, [selectedSet, linkColor]);

    // Link width
    const getLinkWidth = useCallback((link) => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;

        if (selectedSet.has(sourceId) || selectedSet.has(targetId)) {
            return 2;
        }
        return linkWidth || 0.5;
    }, [selectedSet, linkWidth]);

    // Node label
    const getNodeLabel = useCallback((node) => {
        return node.label || node.id;
    }, []);

    return (
        <div
            id={id}
            ref={containerRef}
            style={{
                width: '100%',
                height: '100%',
                minWidth: '400px',
                minHeight: '300px'
            }}
        >
            <ForceGraph2D
                ref={graphRef}
                graphData={graphData}
                width={dimensions.width}
                height={dimensions.height}
                nodeColor={getNodeColor}
                nodeVal={getNodeSize}
                nodeLabel={getNodeLabel}
                linkColor={getLinkColor}
                linkWidth={getLinkWidth}
                linkDirectionalArrowLength={3}
                linkDirectionalArrowRelPos={1}
                onNodeClick={handleNodeClick}
                onBackgroundClick={handleBackgroundClick}
                onNodeRightClick={handleNodeRightClick}
                enableZoomInteraction={enableZoom !== false}
                enablePanInteraction={enablePan !== false}
                enableNodeDrag={enableNodeDrag !== false}
                cooldownTicks={cooldownTicks || 100}
                nodeCanvasObjectMode={() => 'after'}
                nodeCanvasObject={(node, ctx, globalScale) => {
                    // Draw selection ring
                    if (node && selectedSet.has(node.id)) {
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, getNodeSize(node) + 2, 0, 2 * Math.PI);
                        ctx.strokeStyle = '#ffd93d';
                        ctx.lineWidth = 2 / globalScale;
                        ctx.stroke();
                    }
                }}
            />
        </div>
    );
};

ForceGraph.defaultProps = {
    nodes: [],
    links: [],
    selectedNodes: [],
    enableZoom: true,
    enablePan: true,
    enableNodeDrag: true,
    cooldownTicks: 100,
};

export default ForceGraph;
