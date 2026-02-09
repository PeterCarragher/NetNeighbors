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
    const overlayRef = useRef();
    const [graphData, setGraphData] = useState({ nodes: [], links: [] });
    const [selectedSet, setSelectedSet] = useState(new Set(selectedNodes || []));
    const [dimensions, setDimensions] = useState({ width: width || 800, height: height || 600 });

    // Box selection state
    const [isBoxSelecting, setIsBoxSelecting] = useState(false);
    const [boxStart, setBoxStart] = useState(null);
    const [boxEnd, setBoxEnd] = useState(null);
    const [shiftHeld, setShiftHeld] = useState(false);

    // Track shift key globally
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Shift') setShiftHeld(true);
        };
        const handleKeyUp = (e) => {
            if (e.key === 'Shift') setShiftHeld(false);
        };
        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, []);

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

        // Debug: log connection values
        if (nodesCopy.length > 0) {
            const connValues = nodesCopy.map(n => n.connections || 0);
            const maxConn = Math.max(...connValues);
            const minConn = Math.min(...connValues);
            const withConn = connValues.filter(c => c > 0).length;
            console.log(`Nodes: ${nodesCopy.length}, with connections: ${withConn}, min: ${minConn}, max: ${maxConn}`);
        }
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

    // Background click - clear selection (only if not box selecting)
    const handleBackgroundClick = useCallback((event) => {
        if (isBoxSelecting) return;
        setSelectedSet(new Set());
        if (setProps) {
            setProps({ selectedNodes: [] });
        }
    }, [setProps, isBoxSelecting]);

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

    // Node size function - scale by in-degree (connections)
    // nodeVal sets the node's volume; force-graph uses sqrt(nodeVal) for radius
    // So we square our desired size to get the visual we want
    const getNodeSize = useCallback((node) => {
        const connections = node.connections || 0;
        // Base size 3, scale up with connections using sqrt for better distribution
        // Then square it because nodeVal represents area
        const baseSize = 3;
        const scaledSize = baseSize + Math.sqrt(connections) * 2;
        const size = scaledSize * scaledSize; // Square it for nodeVal
        if (selectedSet.has(node.id)) {
            return size * 2; // Larger when selected
        }
        return size;
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

    // Box selection handlers on the overlay
    const handleOverlayMouseDown = useCallback((event) => {
        if (!shiftHeld) return;
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        console.log('Box select start:', { x, y, shiftHeld });
        setIsBoxSelecting(true);
        setBoxStart({ x, y });
        setBoxEnd({ x, y });
        event.preventDefault();
        event.stopPropagation();
    }, [shiftHeld]);

    const handleOverlayMouseMove = useCallback((event) => {
        if (!isBoxSelecting || !containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        setBoxEnd({ x, y });
    }, [isBoxSelecting]);

    const handleOverlayMouseUp = useCallback((event) => {
        console.log('Box select mouseup:', { isBoxSelecting, boxStart, boxEnd, hasGraph: !!graphRef.current });
        if (!isBoxSelecting || !boxStart || !boxEnd || !graphRef.current) {
            setIsBoxSelecting(false);
            return;
        }

        // Get the selection box bounds in screen space
        const minX = Math.min(boxStart.x, boxEnd.x);
        const maxX = Math.max(boxStart.x, boxEnd.x);
        const minY = Math.min(boxStart.y, boxEnd.y);
        const maxY = Math.max(boxStart.y, boxEnd.y);

        console.log('Box bounds:', { minX, maxX, minY, maxY, size: (maxX - minX) * (maxY - minY) });

        // Only select if box is big enough (avoid accidental clicks)
        if (maxX - minX > 5 && maxY - minY > 5) {
            const graph = graphRef.current;
            const selected = [];

            graphData.nodes.forEach(node => {
                if (node.x !== undefined && node.y !== undefined) {
                    // Convert graph coords to screen coords
                    const screenCoords = graph.graph2ScreenCoords(node.x, node.y);
                    if (screenCoords.x >= minX && screenCoords.x <= maxX &&
                        screenCoords.y >= minY && screenCoords.y <= maxY) {
                        selected.push(node.id);
                    }
                }
            });

            console.log('Box selected nodes:', selected.length, selected.slice(0, 5));

            if (selected.length > 0) {
                const newSet = event?.ctrlKey || event?.metaKey
                    ? new Set([...selectedSet, ...selected])
                    : new Set(selected);
                setSelectedSet(newSet);
                if (setProps) {
                    setProps({ selectedNodes: Array.from(newSet) });
                }
            }
        }

        setIsBoxSelecting(false);
        setBoxStart(null);
        setBoxEnd(null);
    }, [isBoxSelecting, boxStart, boxEnd, graphData.nodes, selectedSet, setProps]);

    // Get selection box style
    const getSelectionBoxStyle = () => {
        if (!isBoxSelecting || !boxStart || !boxEnd) return { display: 'none' };
        return {
            position: 'absolute',
            left: Math.min(boxStart.x, boxEnd.x),
            top: Math.min(boxStart.y, boxEnd.y),
            width: Math.abs(boxEnd.x - boxStart.x),
            height: Math.abs(boxEnd.y - boxStart.y),
            border: '2px dashed #667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            pointerEvents: 'none',
            zIndex: 1000,
        };
    };

    return (
        <div
            id={id}
            ref={containerRef}
            style={{
                width: '100%',
                height: '100%',
                minWidth: '400px',
                minHeight: '300px',
                position: 'relative'
            }}
        >
            {/* Invisible overlay for box selection when shift is held */}
            <div
                ref={overlayRef}
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    zIndex: shiftHeld ? 100 : -1,
                    cursor: shiftHeld ? 'crosshair' : 'default',
                    pointerEvents: shiftHeld ? 'auto' : 'none',
                }}
                onMouseDown={handleOverlayMouseDown}
                onMouseMove={handleOverlayMouseMove}
                onMouseUp={handleOverlayMouseUp}
                onMouseLeave={handleOverlayMouseUp}
            />
            {/* Selection box */}
            <div style={getSelectionBoxStyle()} />
            {/* Wrap ForceGraph2D to ensure proper z-stacking with overlay */}
            <div style={{ position: 'relative', zIndex: 1, width: '100%', height: '100%' }}>
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
                        const size = getNodeSize(node);
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, Math.sqrt(size) * 2 + 2, 0, 2 * Math.PI);
                        ctx.strokeStyle = '#ffd93d';
                        ctx.lineWidth = 2 / globalScale;
                        ctx.stroke();
                    }
                }}
            />
            </div>
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
