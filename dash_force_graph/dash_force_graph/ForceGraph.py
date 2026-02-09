"""ForceGraph Dash component."""

from dash.development.base_component import Component, _explicitize_args


class ForceGraph(Component):
    """
    A high-performance graph visualization component using force-graph.

    ForceGraph renders large graphs efficiently using WebGL/Canvas.
    It supports interactive features like node selection, panning, zooming,
    and dynamic graph updates.

    Keyword arguments:
    - id (string): The ID of this component.
    - nodes (list): List of node objects. Each node should have at least 'id'.
        Optional fields: 'label', 'color', 'type', 'connections', 'x', 'y'.
    - links (list): List of link objects. Each link needs 'source' and 'target' (node IDs).
        Optional fields: 'color', 'width'.
    - selectedNodes (list): List of currently selected node IDs. Supports two-way binding.
    - width (number): Width of the graph container in pixels.
    - height (number): Height of the graph container in pixels.
    - nodeColor (string): Default color for nodes. Can also be set per-node.
    - nodeSize (number): Default size for nodes.
    - linkColor (string): Default color for links.
    - linkWidth (number): Default width for links.
    - enableZoom (boolean): Enable zoom interaction (default: True).
    - enablePan (boolean): Enable pan interaction (default: True).
    - enableNodeDrag (boolean): Enable node dragging (default: True).
    - cooldownTicks (number): Simulation ticks before stopping (default: 100).
    - centerAt (string): Node ID to center the view on.
    - zoomLevel (number): Zoom level to apply.
    - rightClickedNode (string): ID of the last right-clicked node (read-only).
    - rightClickPosition (dict): Position {x, y} of the last right-click (read-only).
    """

    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_force_graph'
    _type = 'ForceGraph'

    _js_dist = []
    _css_dist = []

    @_explicitize_args
    def __init__(
        self,
        id=Component.UNDEFINED,
        nodes=Component.UNDEFINED,
        links=Component.UNDEFINED,
        selectedNodes=Component.UNDEFINED,
        width=Component.UNDEFINED,
        height=Component.UNDEFINED,
        nodeColor=Component.UNDEFINED,
        nodeSize=Component.UNDEFINED,
        linkColor=Component.UNDEFINED,
        linkWidth=Component.UNDEFINED,
        enableZoom=Component.UNDEFINED,
        enablePan=Component.UNDEFINED,
        enableNodeDrag=Component.UNDEFINED,
        cooldownTicks=Component.UNDEFINED,
        centerAt=Component.UNDEFINED,
        zoomLevel=Component.UNDEFINED,
        rightClickedNode=Component.UNDEFINED,
        rightClickPosition=Component.UNDEFINED,
        **kwargs
    ):
        self._prop_names = [
            'id',
            'nodes',
            'links',
            'selectedNodes',
            'width',
            'height',
            'nodeColor',
            'nodeSize',
            'linkColor',
            'linkWidth',
            'enableZoom',
            'enablePan',
            'enableNodeDrag',
            'cooldownTicks',
            'centerAt',
            'zoomLevel',
            'rightClickedNode',
            'rightClickPosition',
        ]
        self._valid_wildcard_attributes = []
        self.available_properties = [
            'id',
            'nodes',
            'links',
            'selectedNodes',
            'width',
            'height',
            'nodeColor',
            'nodeSize',
            'linkColor',
            'linkWidth',
            'enableZoom',
            'enablePan',
            'enableNodeDrag',
            'cooldownTicks',
            'centerAt',
            'zoomLevel',
            'rightClickedNode',
            'rightClickPosition',
        ]
        self.available_wildcard_properties = []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        super(ForceGraph, self).__init__(**args)
