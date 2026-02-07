"""
NetNeighbors Graph Explorer with Dash Cytoscape
Full integration with Common Crawl webgraph discovery
"""

import os
import base64
import io
import dash
from dash import html, dcc, Input, Output, State, callback_context, ALL
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto
import json
import xml.etree.ElementTree as ET

from graph_bridge import GraphBridge

def reverse_domain(domain):
    """Reverse domain for Common Crawl format"""
    return '.'.join(reversed(domain.split('.')))


def unreverse_domain(domain):
    """Unreverse domain for display"""
    return '.'.join(reversed(domain.split('.')))


class GraphExplorer:
    """Manages graph state and Common Crawl queries"""

    def __init__(self, bridge=None):
        self.bridge = bridge  # Your JVM bridge instance
        self.hop_counter = 0

    def discover_neighbors(self, seed_domains, min_connections=5, direction='backlinks'):
        """
        Query Common Crawl for neighbors of seed domains

        Args:
            seed_domains: list of domain names (normal format)
            min_connections: minimum connection threshold
            direction: 'backlinks' or 'outlinks'

        Returns:
            (nodes, edges): tuple of new graph elements
        """

        # Convert to reversed format for query
        seed_domains_reversed = [reverse_domain(d) for d in seed_domains]

        # Query the bridge
        results = self.bridge.discover(
            seed_domains=seed_domains_reversed,
            min_connections=min_connections,
            direction=direction
        )

        # Unreverse domain names from CommonCrawl format for display
        for r in results:
            r['domain'] = unreverse_domain(r['domain'])

        # Build graph elements
        nodes, edges = self._build_elements(seed_domains, results, direction)

        return nodes, edges

    def _build_elements(self, seed_domains, results, direction):
        """Convert discovery results to Cytoscape elements"""
        nodes = []
        edges = []

        # Create discovered nodes
        if results:
            max_conn = max(r['connections'] for r in results)
            min_conn = min(r['connections'] for r in results)
            conn_range = max(max_conn - min_conn, 1)

            for result in results:
                domain = result['domain']
                connections = result['connections']

                # Normalize size (20-60 pixel range)
                size = 20 + 40 * (connections - min_conn) / conn_range

                nodes.append({
                    'data': {
                        'id': domain,
                        'label': domain,
                        'type': 'discovered',
                        'hop': self.hop_counter + 1,
                        'connections': connections
                    },
                    'classes': 'discovered'
                })

                # Create edges based on direction
                for seed in seed_domains:
                    if direction == 'backlinks':
                        # discovered -> seed
                        edges.append({
                            'data': {
                                'source': domain,
                                'target': seed
                            }
                        })
                    else:  # outlinks
                        # seed -> discovered
                        edges.append({
                            'data': {
                                'source': seed,
                                'target': domain
                            }
                        })

        self.hop_counter += 1
        return nodes, edges


def get_bridge():
    """Initialize GraphBridge from environment variables."""
    webgraph_dir = os.environ.get("WEBGRAPH_DIR", "/data/webgraph")
    version = os.environ.get("WEBGRAPH_VERSION", "cc-main-2024-feb-apr-may")
    jar_path = os.environ.get("CC_WEBGRAPH_JAR", None)

    bridge = GraphBridge(webgraph_dir, version, jar_path)
    bridge.load_graph()
    return bridge


# Initialize bridge and explorer at startup
bridge = get_bridge()
explorer = GraphExplorer(bridge=bridge)

# Initialize Dash app
app = dash.Dash(__name__, assets_folder='assets')

# Cytoscape stylesheet
stylesheet = [
    # Seed nodes
    {
        'selector': '.seed',
        'style': {
            'background-color': '#ff6b6b',
            'label': 'data(label)',
            'width': 60,
            'height': 60,
            'font-size': 11,
            'color': '#fff',
            'text-outline-color': '#000',
            'text-outline-width': 2,
            'text-halign': 'center',
            'text-valign': 'center'
        }
    },
    # Discovered nodes - hop 1
    {
        'selector': '[hop = 1]',
        'style': {
            'background-color': '#4ecdc4',
            'label': 'data(label)',
            'width': 'mapData(connections, 1, 50, 25, 50)',
            'height': 'mapData(connections, 1, 50, 25, 50)',
            'font-size': 10,
            'color': '#000'
        }
    },
    # Discovered nodes - hop 2
    {
        'selector': '[hop = 2]',
        'style': {
            'background-color': '#95e1d3',
            'label': 'data(label)',
            'width': 'mapData(connections, 1, 50, 25, 50)',
            'height': 'mapData(connections, 1, 50, 25, 50)',
            'font-size': 9,
            'color': '#000'
        }
    },
    # Discovered nodes - hop 3+
    {
        'selector': '[hop >= 3]',
        'style': {
            'background-color': '#a8e6cf',
            'label': 'data(label)',
            'width': 'mapData(connections, 1, 50, 25, 50)',
            'height': 'mapData(connections, 1, 50, 25, 50)',
            'font-size': 8,
            'color': '#000'
        }
    },
    # Selected nodes
    {
        'selector': ':selected',
        'style': {
            'border-width': 4,
            'border-color': '#ffd93d',
            'background-color': '#ffe66d'
        }
    },
    # Edges
    {
        'selector': 'edge',
        'style': {
            'width': 1.5,
            'line-color': '#bdc3c7',
            'target-arrow-color': '#bdc3c7',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.6
        }
    },
    # Highlighted edges (connected to selected nodes)
    {
        'selector': 'edge:selected',
        'style': {
            'line-color': '#ffd93d',
            'target-arrow-color': '#ffd93d',
            'width': 3,
            'opacity': 1
        }
    }
]

# ----- Layout -----

app.layout = html.Div([
    # ===== Navbar =====
    html.Div([
        html.Span("net_neighbor", className='nav-title'),
        html.Div([
            # Export menu
            html.Div([
                html.Span("Export", className='nav-menu-label'),
                html.Div([
                    html.Div('Node List (.csv)', id={'type': 'export-btn', 'index': 'csv-nodes'},
                             className='nav-dropdown-item', n_clicks=0),
                    html.Div('Edge List (.csv)', id={'type': 'export-btn', 'index': 'csv-edges'},
                             className='nav-dropdown-item', n_clicks=0),
                    html.Div('Graph (.gexf)', id={'type': 'export-btn', 'index': 'gexf'},
                             className='nav-dropdown-item', n_clicks=0),
                ], className='nav-dropdown')
            ], className='nav-menu'),

            # Resources menu
            html.Div([
                html.Span("Resources", className='nav-menu-label'),
                html.Div([
                    html.A(html.Div('cc-webgraph (GitHub)', className='nav-dropdown-item'),
                           href='https://github.com/commoncrawl/cc-webgraph',
                           target='_blank'),
                    html.A(html.Div('NetNeighbors (GitHub)', className='nav-dropdown-item'),
                           href='https://github.com/PeterCarragher/NetNeighbors',
                           target='_blank'),
                    html.A(html.Div('NetNeighbors Paper (ACM)', className='nav-dropdown-item'),
                           href='https://dl.acm.org/doi/pdf/10.1145/3670410',
                           target='_blank'),
                ], className='nav-dropdown')
            ], className='nav-menu'),

            # Help menu
            html.Div([
                html.Span("Help", className='nav-menu-label'),
                html.Div([
                    html.Div([html.Strong("Add nodes"), " \u2014 type domains in the left pane textarea, click Add to Viewport"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                    html.Div([html.Strong("Select nodes"), " \u2014 click a node, or box-select by dragging on the canvas"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                    html.Div([html.Strong("Delete nodes"), " \u2014 select nodes, then press Delete or Backspace"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                    html.Div([html.Strong("Discover"), " \u2014 select nodes, right-click \u2192 set options \u2192 Discover"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                ], className='nav-dropdown', style={'min-width': '340px'})
            ], className='nav-menu'),
        ], style={'display': 'flex', 'height': '100%'})
    ], id='navbar'),

    # ===== Body =====
    html.Div([
        # Left Pane
        html.Div([
            # Search box
            dcc.Input(
                id='domain-search',
                type='text',
                placeholder='Search domains...',
                style={
                    'width': '100%',
                    'padding': '8px 12px',
                    'border': 'none',
                    'border-bottom': '1px solid #ddd',
                    'font-size': '13px',
                    'box-sizing': 'border-box',
                    'background': '#fff'
                }
            ),

            # Domain list (fills available space)
            html.Div(id='domain-list-container', children=[
                html.Div(
                    "No domains yet. Add some below.",
                    style={'color': '#999', 'font-style': 'italic', 'padding': '20px', 'text-align': 'center'}
                )
            ]),

            # Bottom section: textarea + buttons
            html.Div([
                dcc.Textarea(
                    id='new-domains-input',
                    placeholder='Enter new domains...\none per line',
                    style={
                        'width': '100%',
                        'height': '80px',
                        'padding': '8px',
                        'border': '1px solid #ddd',
                        'border-radius': '4px',
                        'font-family': 'monospace',
                        'font-size': '12px',
                        'resize': 'vertical',
                        'box-sizing': 'border-box'
                    }
                ),
                html.Div([
                    dcc.Upload(
                        id='file-upload',
                        children=html.Button('Import from File', style={
                            'padding': '6px 10px',
                            'background': '#95a5a6',
                            'color': 'white',
                            'border': 'none',
                            'border-radius': '4px',
                            'cursor': 'pointer',
                            'font-size': '12px'
                        }),
                        multiple=False
                    ),
                    html.Button('Add to Viewport', id='add-viewport-btn', n_clicks=0, style={
                        'padding': '6px 10px',
                        'background': '#4ecdc4',
                        'color': 'white',
                        'border': 'none',
                        'border-radius': '4px',
                        'cursor': 'pointer',
                        'font-size': '12px',
                        'font-weight': 'bold'
                    })
                ], style={
                    'display': 'flex',
                    'gap': '6px',
                    'margin-top': '6px',
                    'justify-content': 'space-between'
                })
            ], style={
                'padding': '10px',
                'flex-shrink': 0
            })

        ], id='left-pane'),

        # Right Pane: graph + context menu
        html.Div([
            cyto.Cytoscape(
                id='cytoscape-graph',
                layout={
                    'name': 'cose',
                    'animate': True,
                    'animationDuration': 500,
                    'nodeRepulsion': 400000,
                    'idealEdgeLength': 100,
                    'edgeElasticity': 100,
                    'nestingFactor': 5,
                    'gravity': 80,
                    'numIter': 1000,
                    'initialTemp': 200,
                    'coolingFactor': 0.95,
                    'minTemp': 1.0
                },
                style={'width': '100%', 'height': '100%', 'background': '#f8f9fa'},
                elements=[],
                stylesheet=stylesheet,
                boxSelectionEnabled=True,
                autoungrabify=False,
                userZoomingEnabled=True,
                userPanningEnabled=True
            ),

            # Context menu (hidden by default, positioned by JS)
            html.Div([
                html.H4("Discovery Settings"),
                html.Div([
                    html.Label("Direction:", style={'font-weight': 'bold', 'font-size': '13px'}),
                    dcc.RadioItems(
                        id='ctx-direction-radio',
                        options=[
                            {'label': ' Backlinks', 'value': 'backlinks'},
                            {'label': ' Outlinks', 'value': 'outlinks'}
                        ],
                        value='backlinks',
                        style={'margin': '6px 0', 'font-size': '13px'}
                    )
                ]),
                html.Div([
                    html.Label("Min Connections:", style={'font-weight': 'bold', 'font-size': '13px'}),
                    dcc.Slider(
                        id='ctx-min-conn-slider',
                        min=1,
                        max=10,
                        step=1,
                        value=5,
                        marks={1: '1', 5: '5', 10: '10'},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], style={'margin': '8px 0'}),
                html.Div(id='ctx-selection-count',
                         children='0 node(s) selected',
                         style={'font-size': '12px', 'color': '#666', 'margin': '6px 0'}),
                html.Button('Discover', id='discover-btn', n_clicks=0, style={
                    'width': '100%',
                    'padding': '10px',
                    'background': '#667eea',
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'font-size': '14px',
                    'font-weight': 'bold',
                    'margin-top': '6px'
                })
            ], id='context-menu', style={'display': 'none'})
        ], id='graph-wrapper'),

    ], id='body-container'),

    # Hidden elements
    html.Button(id='delete-trigger-btn', style={'display': 'none'}, n_clicks=0),
    dcc.Store(id='focus-domain', data=None),
    dcc.Store(id='center-ack', data=None),
    dcc.Store(id='pending-elements', data=None),
    dcc.ConfirmDialog(id='confirm-dialog', message=''),
    dcc.Download(id='export-download'),
], id='root-container')


# ----- Callbacks -----

# CB1: Domain List (elements + search → domain-list children)
@app.callback(
    Output('domain-list-container', 'children'),
    [Input('cytoscape-graph', 'elements'),
     Input('domain-search', 'value')]
)
def update_domain_list(elements, search_text):
    if not elements:
        return html.Div(
            "No domains yet. Add some below.",
            style={'color': '#999', 'font-style': 'italic', 'padding': '20px', 'text-align': 'center'}
        )

    # Extract node IDs
    domains = sorted([
        e['data']['id'] for e in elements
        if 'source' not in e['data']
    ])

    # Filter by search
    if search_text:
        query = search_text.lower()
        domains = [d for d in domains if query in d.lower()]

    if not domains:
        return html.Div(
            "No matching domains.",
            style={'color': '#999', 'font-style': 'italic', 'padding': '20px', 'text-align': 'center'}
        )

    return [
        html.Div(
            domain,
            id={'type': 'domain-item', 'index': domain},
            className='domain-item',
            n_clicks=0
        )
        for domain in domains
    ]


# CB2: Domain Click → Focus Store
@app.callback(
    Output('focus-domain', 'data'),
    Input({'type': 'domain-item', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def domain_click_to_focus(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    # Find which item was clicked
    prop_id = ctx.triggered[0]['prop_id']
    # prop_id looks like '{"index":"cnn.com","type":"domain-item"}.n_clicks'
    clicked_id = json.loads(prop_id.rsplit('.', 1)[0])
    domain = clicked_id['index']
    return domain


# CB3: Center Viewport (clientside callback)
app.clientside_callback(
    """
    function(focusDomain) {
        if (!focusDomain) return null;
        // Access the Cytoscape instance via Dash Cytoscape's internal registry
        var cyEl = document.getElementById('cytoscape-graph');
        if (!cyEl || !cyEl._cyreg || !cyEl._cyreg.cy) return null;
        var cy = cyEl._cyreg.cy;
        // Deselect all, then select and center target
        cy.elements().unselect();
        var node = cy.getElementById(focusDomain);
        if (node && node.length) {
            node.select();
            cy.animate({center: {eles: node}, duration: 300});
        }
        return focusDomain;
    }
    """,
    Output('center-ack', 'data'),
    Input('focus-domain', 'data'),
    prevent_initial_call=True
)


# CB4: Import File + Add to Viewport
@app.callback(
    [Output('cytoscape-graph', 'elements', allow_duplicate=True),
     Output('new-domains-input', 'value')],
    [Input('file-upload', 'contents'),
     Input('add-viewport-btn', 'n_clicks')],
    [State('file-upload', 'filename'),
     State('new-domains-input', 'value'),
     State('cytoscape-graph', 'elements')],
    prevent_initial_call=True
)
def import_and_add(file_contents, add_clicks, filename, textarea_value, current_elements):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger == 'file-upload' and file_contents:
        # Decode uploaded file (text)
        content_type, content_string = file_contents.split(',')
        decoded = base64.b64decode(content_string).decode('utf-8')
        # Populate textarea with file contents (don't modify graph yet)
        return current_elements or [], decoded

    if trigger == 'add-viewport-btn':
        if not textarea_value or not textarea_value.strip():
            raise PreventUpdate

        # Parse domains from textarea
        new_domains = [d.strip() for d in textarea_value.split('\n') if d.strip()]
        if not new_domains:
            raise PreventUpdate

        elements = list(current_elements) if current_elements else []
        existing_ids = {
            e['data']['id'] for e in elements if 'source' not in e['data']
        }

        for domain in new_domains:
            if domain not in existing_ids:
                elements.append({
                    'data': {
                        'id': domain,
                        'label': domain,
                        'type': 'seed',
                        'hop': 0
                    },
                    'classes': 'seed'
                })
                existing_ids.add(domain)

        return elements, ''

    raise PreventUpdate


# CB5: Slider Max Update based on selection count
@app.callback(
    [Output('ctx-min-conn-slider', 'max'),
     Output('ctx-min-conn-slider', 'value'),
     Output('ctx-min-conn-slider', 'marks'),
     Output('ctx-selection-count', 'children')],
    Input('cytoscape-graph', 'selectedNodeData')
)
def update_slider_max(selected_nodes):
    count = len(selected_nodes) if selected_nodes else 0
    max_val = max(count, 1)
    # Clamp current value
    value = min(5, max_val)
    # Build marks
    marks = {1: '1'}
    if max_val > 1:
        mid = max_val // 2
        if mid > 1:
            marks[mid] = str(mid)
        marks[max_val] = str(max_val)
    label = f"{count} node(s) selected"
    return max_val, value, marks, label


NODE_WARNING_THRESHOLD = 150

# CB6: Context Menu Discover (with large-result warning)
@app.callback(
    [Output('cytoscape-graph', 'elements', allow_duplicate=True),
     Output('pending-elements', 'data'),
     Output('confirm-dialog', 'displayed'),
     Output('confirm-dialog', 'message')],
    Input('discover-btn', 'n_clicks'),
    [State('cytoscape-graph', 'selectedNodeData'),
     State('ctx-direction-radio', 'value'),
     State('ctx-min-conn-slider', 'value'),
     State('cytoscape-graph', 'elements')],
    prevent_initial_call=True
)
def context_menu_discover(n_clicks, selected_nodes, direction, min_conn, current_elements):
    if not n_clicks or not selected_nodes:
        raise PreventUpdate

    seed_domains = [node['id'] for node in selected_nodes]
    new_nodes, new_edges = explorer.discover_neighbors(seed_domains, min_conn, direction)

    elements = list(current_elements) if current_elements else []
    existing_ids = {
        e['data']['id'] for e in elements if 'source' not in e['data']
    }
    unique_nodes = [n for n in new_nodes if n['data']['id'] not in existing_ids]

    if len(unique_nodes) > NODE_WARNING_THRESHOLD:
        msg = (f"This will add {len(unique_nodes)} nodes to the viewport, "
               f"which may affect the visualizer's performance. Continue?")
        return elements, {'nodes': unique_nodes, 'edges': new_edges}, True, msg

    elements.extend(unique_nodes)
    elements.extend(new_edges)
    return elements, None, False, ''


# CB10: Confirm large discovery
@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    Input('confirm-dialog', 'submit_n_clicks'),
    [State('pending-elements', 'data'),
     State('cytoscape-graph', 'elements')],
    prevent_initial_call=True
)
def confirm_large_discovery(submit_clicks, pending, current_elements):
    if not submit_clicks or not pending:
        raise PreventUpdate

    elements = list(current_elements) if current_elements else []
    existing_ids = {
        e['data']['id'] for e in elements if 'source' not in e['data']
    }

    for node in pending['nodes']:
        if node['data']['id'] not in existing_ids:
            elements.append(node)
            existing_ids.add(node['data']['id'])
    elements.extend(pending['edges'])

    return elements


# CB7: Hide context menu on Discover (clientside)
app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) return null;
        var menu = document.getElementById('context-menu');
        if (menu) menu.style.display = 'none';
        return null;
    }
    """,
    Output('center-ack', 'data', allow_duplicate=True),
    Input('discover-btn', 'n_clicks'),
    prevent_initial_call=True
)


# CB8: Delete Selected Nodes (via hidden button clicked by JS on Delete keypress)
@app.callback(
    Output('cytoscape-graph', 'elements', allow_duplicate=True),
    Input('delete-trigger-btn', 'n_clicks'),
    [State('cytoscape-graph', 'selectedNodeData'),
     State('cytoscape-graph', 'elements')],
    prevent_initial_call=True
)
def delete_selected_nodes(n_clicks, selected_nodes, current_elements):
    if not n_clicks or not selected_nodes:
        raise PreventUpdate

    selected_ids = {node['id'] for node in selected_nodes}

    filtered = [
        e for e in current_elements
        if (
            ('source' not in e['data'] and e['data']['id'] not in selected_ids) or
            ('source' in e['data'] and
             e['data']['source'] not in selected_ids and
             e['data']['target'] not in selected_ids)
        )
    ]

    return filtered


# CB9: Export Download
@app.callback(
    Output('export-download', 'data'),
    Input({'type': 'export-btn', 'index': ALL}, 'n_clicks'),
    State('cytoscape-graph', 'elements'),
    prevent_initial_call=True
)
def export_graph(n_clicks_list, elements):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    prop_id = ctx.triggered[0]['prop_id']
    clicked_id = json.loads(prop_id.rsplit('.', 1)[0])
    fmt = clicked_id['index']

    if not elements:
        raise PreventUpdate

    nodes = [e for e in elements if 'source' not in e['data']]
    edges = [e for e in elements if 'source' in e['data']]

    if fmt == 'csv-nodes':
        lines = ['domain,type,hop,connections']
        for n in nodes:
            d = n['data']
            lines.append(f"{d['id']},{d.get('type','')},{d.get('hop','')},{d.get('connections','')}")
        return dict(content='\n'.join(lines), filename='nodes.csv')

    elif fmt == 'csv-edges':
        lines = ['source,target']
        for e in edges:
            lines.append(f"{e['data']['source']},{e['data']['target']}")
        return dict(content='\n'.join(lines), filename='edges.csv')

    elif fmt == 'gexf':
        root = ET.Element('gexf', xmlns='http://www.gexf.net/1.2draft', version='1.2')
        graph_el = ET.SubElement(root, 'graph', defaultedgetype='directed')

        # Node attributes
        attrs = ET.SubElement(graph_el, 'attributes', {'class': 'node'})
        ET.SubElement(attrs, 'attribute', id='0', title='type', type='string')
        ET.SubElement(attrs, 'attribute', id='1', title='hop', type='integer')
        ET.SubElement(attrs, 'attribute', id='2', title='connections', type='integer')

        nodes_el = ET.SubElement(graph_el, 'nodes')
        for n in nodes:
            d = n['data']
            node_el = ET.SubElement(nodes_el, 'node', id=d['id'], label=d.get('label', d['id']))
            av = ET.SubElement(node_el, 'attvalues')
            ET.SubElement(av, 'attvalue', {'for': '0', 'value': str(d.get('type', ''))})
            ET.SubElement(av, 'attvalue', {'for': '1', 'value': str(d.get('hop', ''))})
            ET.SubElement(av, 'attvalue', {'for': '2', 'value': str(d.get('connections', ''))})

        edges_el = ET.SubElement(graph_el, 'edges')
        for i, e in enumerate(edges):
            ET.SubElement(edges_el, 'edge', id=str(i),
                          source=e['data']['source'], target=e['data']['target'])

        buf = io.StringIO()
        tree = ET.ElementTree(root)
        tree.write(buf, encoding='unicode', xml_declaration=True)
        return dict(content=buf.getvalue(), filename='graph.gexf')

    raise PreventUpdate


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=8050)
