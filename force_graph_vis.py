"""
NetNeighbors Graph Explorer with Force Graph
High-performance graph visualization using WebGL via force-graph
"""

import os
import re
import sys
import base64
import io
import pickle
import networkx as nx
import dash
from dash import html, dcc, Input, Output, State, callback_context, ALL, ClientsideFunction
from dash.exceptions import PreventUpdate
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from dash_force_graph import ForceGraph
from pyccwebgraph import CCWebgraph

# Add examples directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "examples"))

# Path to precomputed example graphs
PICKLE_DIR = Path(__file__).parent / "examples" / "pickle"

# Large graph thresholds (moved from JS component)
LARGE_GRAPH_NODE_THRESHOLD = 10000
LARGE_GRAPH_EDGE_THRESHOLD = 20000

# Node colors
SEED_COLOR = '#ff6b6b'
DISCOVERED_COLOR = '#4ecdc4'

# Hop color palette (index 0 = hop 1, index 1 = hop 2, etc.)
HOP_COLORS = [
    '#4ecdc4',  # hop 1 – teal
    '#667eea',  # hop 2 – indigo
    '#f9ca24',  # hop 3 – yellow
    '#f0932b',  # hop 4 – orange
    '#6ab04c',  # hop 5 – green
    '#e056fd',  # hop 6 – purple
    '#22a6b3',  # hop 7 – cyan
    '#eb4d4b',  # hop 8 – red
]


def hop_color(hop: int) -> str:
    """Return a color for the given hop number (1-indexed)."""
    if hop <= 0:
        return SEED_COLOR
    return HOP_COLORS[(hop - 1) % len(HOP_COLORS)]

# Regex for a well-formed domain
DOMAIN_RE = re.compile(
    r'^(?!-)'
    r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)'
    r'+[a-zA-Z]{2,}$'
)


class GraphExplorer:
    """Manages graph state and Common Crawl queries via pyccwebgraph"""

    def __init__(self, webgraph):
        self.webgraph = webgraph
        self.hop_counter = 0

    def discover_neighbors(self, seed_domains, min_connections=5, direction='backlinks'):
        """Query Common Crawl for neighbors of seed domains."""
        result = self.webgraph.discover(
            seed_domains=seed_domains,
            min_connections=min_connections,
            direction=direction
        )
        nodes, links = self._build_elements(seed_domains, result)
        return nodes, links

    def _build_elements(self, _seed_domains, result):
        """Convert DiscoveryResult to nodes and links"""
        nodes = []
        links = []

        if result.nodes:
            # Count in-degree for each node from the edges
            in_degree = {}
            for src, tgt in result.edges:
                in_degree[tgt] = in_degree.get(tgt, 0) + 1

            for node_data in result.nodes:
                domain = node_data['domain']
                # Use in-degree as connections (how many edges point to this node)
                connections = in_degree.get(domain, 0)

                nodes.append({
                    'id': domain,
                    'label': domain,
                    'type': 'discovered',
                    'hop': self.hop_counter + 1,
                    'connections': connections
                })

            for src, tgt in result.edges:
                links.append({
                    'source': src,
                    'target': tgt
                })

        return nodes, links


def get_webgraph():
    """Initialize CCWebgraph from environment variables."""
    webgraph_dir = os.environ.get("WEBGRAPH_DIR", "/data/webgraph")
    version = os.environ.get("WEBGRAPH_VERSION", "cc-main-2024-feb-apr-may")
    jar_path = os.environ.get("CC_WEBGRAPH_JAR", None)

    wg = CCWebgraph(webgraph_dir, version, jar_path)
    wg.load_graph()
    return wg


# Initialize webgraph and explorer at startup
webgraph = get_webgraph()
explorer = GraphExplorer(webgraph=webgraph)

# Initialize Dash app
app = dash.Dash(__name__, assets_folder='assets', title='NetNeighbors', suppress_callback_exceptions=True)

# URL to example type mapping
EXAMPLE_MAP = {
    '/link-spam-network': 'link-spam',
    '/high-profile-news-network': 'high-profile',
    '/iranian-news-network': 'iranian',
    '/pravda-network': 'pravda',
    '/think-tanks': 'think-tanks',
}
EXAMPLE_NAMES = {
    'link-spam': 'Link Spam Network',
    'high-profile': 'High-Profile News Network',
    'iranian': 'Iranian News Network',
    'pravda': 'Pravda Network',
    'think-tanks': 'Think Tanks',
}

# ----- Layout -----
app.layout = html.Div([
    # ===== Navbar =====
    html.Div([
        html.Span("net_neighbor", className='nav-title'),
        html.Div([
            # Examples menu
            html.Div([
                html.Span("examples", className='nav-menu-label'),
                html.Div([
                    html.Div([
                        dcc.Link('Link Spam Network', href='/link-spam-network', className='example-name'),
                        html.A('paper', href='https://dl.acm.org/doi/10.1145/3670410',
                               target='_blank', className='example-paper-link')
                    ], className='nav-dropdown-item example-item'),
                    html.Div([
                        dcc.Link('High-Profile News', href='/high-profile-news-network', className='example-name'),
                        html.A('paper', href='https://ojs.aaai.org/index.php/ICWSM/article/view/31309',
                               target='_blank', className='example-paper-link')
                    ], className='nav-dropdown-item example-item'),
                    html.Div([
                        dcc.Link('Iranian News Network (.ir)', href='/iranian-news-network', className='example-name'),
                        html.A('paper', href='https://link.springer.com/chapter/10.1007/978-3-031-72241-7_15',
                               target='_blank', className='example-paper-link')
                    ], className='nav-dropdown-item example-item'),
                    html.Div([
                        dcc.Link('Pravda Network (.ru, .ua)', href='/pravda-network', className='example-name'),
                        html.A('paper', href='https://link.springer.com/chapter/10.1007/978-3-032-07715-8_8',
                               target='_blank', className='example-paper-link')
                    ], className='nav-dropdown-item example-item'),
                    html.Div([
                        dcc.Link('Think Tanks (.ru, .ca, .org)', href='/think-tanks', className='example-name'),
                        html.A('paper', href='https://misinforeview.hks.harvard.edu/article/search-engine-manipulation-to-spread-pro-kremlin-propaganda/',
                               target='_blank', className='example-paper-link')
                    ], className='nav-dropdown-item example-item'),
                ], className='nav-dropdown')
            ], className='nav-menu'),

            # Export menu
            html.Div([
                html.Span("export", className='nav-menu-label'),
                html.Div([
                    html.Div('node list (.csv)', id={'type': 'export-btn', 'index': 'csv-nodes'},
                             className='nav-dropdown-item', n_clicks=0),
                    html.Div('edge list (.csv)', id={'type': 'export-btn', 'index': 'csv-edges'},
                             className='nav-dropdown-item', n_clicks=0),
                    html.Div('graph (.gexf)', id={'type': 'export-btn', 'index': 'gexf'},
                             className='nav-dropdown-item', n_clicks=0),
                ], className='nav-dropdown')
            ], className='nav-menu'),

            # Resources menu
            html.Div([
                html.Span("resources", className='nav-menu-label'),
                html.Div([
                    html.A(html.Div('cc-webgraph (github)', className='nav-dropdown-item'),
                           href='https://github.com/commoncrawl/cc-webgraph',
                           target='_blank'),
                    html.A(html.Div('net_neighbor (github)', className='nav-dropdown-item'),
                           href='https://github.com/PeterCarragher/NetNeighbors',
                           target='_blank'),
                    html.A(html.Div('net_neighbor paper (acm)', className='nav-dropdown-item'),
                           href='https://dl.acm.org/doi/pdf/10.1145/3670410',
                           target='_blank'),
                ], className='nav-dropdown')
            ], className='nav-menu'),

            # Help menu
            html.Div([
                html.Span("help", className='nav-menu-label'),
                html.Div([
                    html.Div([html.Strong("add nodes"), " — type domains in the left pane, click add to viewport"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                    html.Div([html.Strong("select nodes"), " — click a node (Ctrl/Cmd for multi-select)"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                    html.Div([html.Strong("find node"), " — click a domain in the left pane to highlight"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                    html.Div([html.Strong("delete nodes"), " — select nodes, click delete button"],
                             className='nav-dropdown-item', style={'cursor': 'default'}),
                    html.Div([html.Strong("discover"), " — select nodes, set options, click discover"],
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
                placeholder='search domains...',
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

            # Domain list
            html.Div(id='domain-list-container', children=[
                html.Div(
                    "no domains yet. add some below.",
                    style={'color': '#999', 'font-style': 'italic', 'padding': '20px', 'text-align': 'center'}
                )
            ]),

            # Bottom section: textarea + buttons
            html.Div([
                dcc.Textarea(
                    id='new-domains-input',
                    placeholder='enter new domains...\none per line',
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
                        children=html.Button('import from file', style={
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
                    html.Button('add to viewport', id='add-viewport-btn', n_clicks=0, style={
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

        # Right Pane: graph + controls
        html.Div([
            # Control panel (replaces context menu)
            html.Div([
                html.Div([
                    html.Label("direction:", style={'fontWeight': 'bold', 'fontSize': '13px', 'marginRight': '8px'}),
                    dcc.RadioItems(
                        id='direction-radio',
                        options=[
                            {'label': ' backlinks', 'value': 'backlinks'},
                            {'label': ' outlinks', 'value': 'outlinks'}
                        ],
                        value='backlinks',
                        inline=True,
                        style={'fontSize': '13px', 'display': 'inline-flex', 'gap': '10px'}
                    )
                ], style={'marginRight': '20px', 'display': 'flex', 'alignItems': 'center'}),
                html.Div([
                    html.Label("min connections:", style={'font-weight': 'bold', 'font-size': '13px'}),
                    dcc.Input(
                        id='min-conn-input',
                        type='number',
                        value=5,
                        min=1,
                        max=100,
                        style={'width': '60px', 'marginLeft': '8px'}
                    )
                ], style={'marginRight': '20px'}),
                html.Div(id='selection-count',
                         children='0 selected',
                         style={'font-size': '13px', 'color': '#666', 'marginRight': '20px'}),
                html.Button('discover', id='discover-btn', n_clicks=0, style={
                    'padding': '8px 16px',
                    'background': '#667eea',
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'font-size': '13px',
                    'font-weight': 'bold',
                    'marginRight': '10px'
                }),
                html.Button('delete selected', id='delete-btn', n_clicks=0, style={
                    'padding': '8px 16px',
                    'background': '#e74c3c',
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'font-size': '13px',
                    'marginRight': '10px',
                }),
                html.Button('show domain names', id='show-labels-btn', n_clicks=0, style={
                    'padding': '8px 16px',
                    'background': 'white',
                    'color': '#444',
                    'border': '2px solid #ddd',
                    'border-radius': '5px',
                    'cursor': 'pointer',
                    'font-size': '13px',
                }),
            ], id='control-panel', style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '10px 15px',
                'background': '#f8f9fa',
                'borderBottom': '1px solid #ddd'
            }),

            # Graph container
            html.Div([
                ForceGraph(
                    id='force-graph',
                    nodes=[],
                    links=[],
                    selectedNodes=[],
                    width=None,  # Will be set by clientside callback
                    height=None,
                    nodeColor=SEED_COLOR,
                    showNeighborLabels=False,
                ),
                html.Div(id='graph-legend', children=[], style={
                    'position': 'absolute',
                    'bottom': '16px',
                    'right': '16px',
                    'background': 'rgba(255,255,255,0.92)',
                    'border': '1px solid #ddd',
                    'border-radius': '6px',
                    'padding': '8px 12px',
                    'font-size': '15px',
                    'display': 'none',
                    'z-index': '10',
                }),
            ], id='graph-container', style={'flex': '1', 'position': 'relative'}),

        ], id='graph-wrapper'),

    ], id='body-container'),

    # Hidden stores
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='graph-nodes', data=[]),
    dcc.Store(id='graph-links', data=[]),
    dcc.Store(id='focus-domain', data=None),
    dcc.Store(id='example-loading', data=None),
    dcc.Store(id='pending-example', data=None),
    dcc.Store(id='last-clicked-domain', data=None),
    dcc.Store(id='legend-labels', data={}),
    dcc.ConfirmDialog(id='confirm-dialog', message=''),
    dcc.ConfirmDialog(id='validation-report', message=''),
    dcc.ConfirmDialog(id='example-confirm', message=''),
    dcc.Download(id='export-download'),

    # Loading overlay
    html.Div([
        html.Div([
            html.Div(className='loading-spinner'),
            html.Div("Loading...", style={'margin-top': '15px', 'color': '#667eea'})
        ], style={'text-align': 'center'})
    ], id='loading-overlay', style={'display': 'none'}),

], id='root-container')


# ----- Callbacks -----

# Sync nodes/links stores to ForceGraph component
@app.callback(
    [Output('force-graph', 'nodes'),
     Output('force-graph', 'links'),
     Output('force-graph', 'mode'),
     Output('force-graph', 'selectedNodes', allow_duplicate=True)],
    [Input('graph-nodes', 'data'),
     Input('graph-links', 'data')],
    prevent_initial_call=True
)
def sync_graph_data(nodes, links):
    nodes = nodes or []
    links = links or []

    # Set node colors based on hop (0 = seed, 1+ = discovery hops)
    for node in nodes:
        node['color'] = hop_color(node.get('hop', 0))

    # Determine mode based on graph size
    is_large = (len(nodes) > LARGE_GRAPH_NODE_THRESHOLD or
                len(links) > LARGE_GRAPH_EDGE_THRESHOLD)
    mode = 'performance' if is_large else 'interactive'

    # no_update preserves whatever selectedNodes the client currently has
    return nodes, links, mode, dash.no_update


# Legend: rebuild whenever nodes or stored labels change
@app.callback(
    [Output('graph-legend', 'children'),
     Output('graph-legend', 'style')],
    Input('graph-nodes', 'data'),
    State('legend-labels', 'data'),
)
def update_legend(nodes, legend_labels):
    base_style = {
        'position': 'absolute',
        'bottom': '16px',
        'right': '16px',
        'background': 'rgba(255,255,255,0.92)',
        'border': '1px solid #ddd',
        'border-radius': '6px',
        'padding': '10px 16px',
        'font-size': '15px',
        'min-width': '180px',
        'z-index': '10',
    }

    if not nodes:
        return [], {**base_style, 'display': 'none'}

    hops_present = sorted({n.get('hop', 0) for n in nodes})
    legend_labels = legend_labels or {}

    rows = []
    for hop in hops_present:
        color = hop_color(hop)
        default_label = 'seed' if hop == 0 else f'hop {hop}'
        label = legend_labels.get(str(hop), default_label)
        rows.append(html.Div(
            [
                # Swatch — click to select all nodes of this hop
                html.Span(
                    id={'type': 'legend-swatch', 'index': hop},
                    n_clicks=0,
                    title='click to select all',
                    style={
                        'display': 'inline-block',
                        'width': '11px',
                        'height': '11px',
                        'border-radius': '50%',
                        'background': color,
                        'margin-right': '7px',
                        'flex-shrink': '0',
                        'cursor': 'pointer',
                    }
                ),
                # Label — click/double-click to rename
                dcc.Input(
                    id={'type': 'legend-label', 'index': hop},
                    value=label,
                    type='text',
                    debounce=True,
                    className='legend-label-input',
                ),
            ],
            style={
                'display': 'flex',
                'align-items': 'center',
                'margin-bottom': '4px',
            }
        ))

    return rows, {**base_style, 'display': 'block'}


# Swatch click → select all nodes of that hop
@app.callback(
    Output('force-graph', 'selectedNodes', allow_duplicate=True),
    Input({'type': 'legend-swatch', 'index': ALL}, 'n_clicks'),
    State('graph-nodes', 'data'),
    prevent_initial_call=True
)
def legend_select_hop(n_clicks_list, nodes):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate
    prop_id = ctx.triggered[0]['prop_id']
    hop = json.loads(prop_id.rsplit('.', 1)[0])['index']
    nodes = nodes or []
    return [n['id'] for n in nodes if n.get('hop', 0) == hop]


# Legend label rename — persist to store when input blurs or Enter is pressed
@app.callback(
    Output('legend-labels', 'data'),
    Input({'type': 'legend-label', 'index': ALL}, 'value'),
    State('legend-labels', 'data'),
    prevent_initial_call=True
)
def save_legend_label(values, current_labels):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    current_labels = dict(current_labels or {})
    prop_id = ctx.triggered[0]['prop_id']
    hop = json.loads(prop_id.rsplit('.', 1)[0])['index']
    value = ctx.triggered[0]['value']
    if value is None:
        raise PreventUpdate
    current_labels[str(hop)] = value
    return current_labels


# Update domain list from nodes
@app.callback(
    Output('domain-list-container', 'children'),
    [Input('graph-nodes', 'data'),
     Input('domain-search', 'value'),
     Input('force-graph', 'selectedNodes')]
)
def update_domain_list(nodes, search_text, selected_nodes):
    if not nodes:
        return html.Div(
            "no domains yet. add some below.",
            style={'color': '#999', 'font-style': 'italic', 'padding': '20px', 'text-align': 'center'}
        )

    domains = sorted([n['id'] for n in nodes])

    if search_text:
        query = search_text.lower()
        domains = [d for d in domains if query in d.lower()]

    if not domains:
        return html.Div(
            "no matching domains.",
            style={'color': '#999', 'font-style': 'italic', 'padding': '20px', 'text-align': 'center'}
        )

    selected_set = set(selected_nodes or [])
    return [
        html.Div(
            domain,
            id={'type': 'domain-item', 'index': domain},
            className='domain-item selected' if domain in selected_set else 'domain-item',
            n_clicks=0
        )
        for domain in domains
    ]


# Domain click -> multi-select with Ctrl/Shift, center on clicked node
app.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='domain_click_handler'),
    [Output('force-graph', 'centerAt'),
     Output('force-graph', 'selectedNodes', allow_duplicate=True),
     Output('last-clicked-domain', 'data')],
    Input({'type': 'domain-item', 'index': ALL}, 'n_clicks'),
    [State('force-graph', 'selectedNodes'),
     State('graph-nodes', 'data'),
     State('domain-search', 'value'),
     State('last-clicked-domain', 'data')],
    prevent_initial_call=True
)


# Show domain names toggle — updates button style and ForceGraph prop together
app.clientside_callback(
    """
    function(n_clicks) {
        var on = n_clicks % 2 === 1;
        var style = {
            padding: '8px 16px',
            background: on ? '#eef2ff' : 'white',
            color: on ? '#667eea' : '#444',
            border: on ? '2px solid #667eea' : '2px solid #ddd',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: on ? 'bold' : 'normal',
        };
        return [on, style];
    }
    """,
    [Output('force-graph', 'showNeighborLabels'),
     Output('show-labels-btn', 'style')],
    Input('show-labels-btn', 'n_clicks'),
    prevent_initial_call=True,
)


# Selection count display
@app.callback(
    Output('selection-count', 'children'),
    Input('force-graph', 'selectedNodes')
)
def update_selection_count(selected):
    count = len(selected) if selected else 0
    return f"{count} selected"


# Import file + Add to viewport
@app.callback(
    [Output('graph-nodes', 'data', allow_duplicate=True),
     Output('graph-links', 'data', allow_duplicate=True),
     Output('new-domains-input', 'value'),
     Output('validation-report', 'displayed'),
     Output('validation-report', 'message')],
    [Input('file-upload', 'contents'),
     Input('add-viewport-btn', 'n_clicks')],
    [State('file-upload', 'filename'),
     State('new-domains-input', 'value'),
     State('graph-nodes', 'data'),
     State('graph-links', 'data')],
    prevent_initial_call=True
)
def import_and_add(file_contents, add_clicks, filename, textarea_value, current_nodes, current_links):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    no_report = (False, '')
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    current_nodes = current_nodes or []
    current_links = current_links or []

    if trigger == 'file-upload' and file_contents:
        _, content_string = file_contents.split(',')
        decoded = base64.b64decode(content_string).decode('utf-8')
        return current_nodes, current_links, decoded, *no_report

    if trigger == 'add-viewport-btn':
        if not textarea_value or not textarea_value.strip():
            raise PreventUpdate

        raw_domains = [d.strip() for d in textarea_value.split('\n') if d.strip()]
        if not raw_domains:
            raise PreventUpdate

        total_input = len(raw_domains)
        well_formed = [d for d in raw_domains if DOMAIN_RE.match(d)]

        if well_formed:
            in_cc, _ = webgraph.validate_seeds(well_formed)
        else:
            in_cc = []

        existing_ids = {n['id'] for n in current_nodes}
        added = []

        for domain in in_cc:
            if domain not in existing_ids:
                current_nodes.append({
                    'id': domain,
                    'label': domain,
                    'type': 'seed',
                    'hop': 0,
                    'connections': 0
                })
                existing_ids.add(domain)
                added.append(domain)

        n_well_formed = len(well_formed)
        n_in_cc = len(in_cc)
        n_added = len(added)

        if n_well_formed < total_input or n_in_cc < n_well_formed:
            msg = (
                f"of {total_input} input domain(s):\n"
                f"  - {n_well_formed} well-formed\n"
                f"  - {n_in_cc} found in commoncrawl data\n"
                f"  - {n_added} imported to viewport"
            )
            return current_nodes, current_links, '', True, msg

        return current_nodes, current_links, '', *no_report

    raise PreventUpdate


# Discover neighbors
@app.callback(
    [Output('graph-nodes', 'data', allow_duplicate=True),
     Output('graph-links', 'data', allow_duplicate=True),
     Output('force-graph', 'selectedNodes', allow_duplicate=True)],
    Input('discover-btn', 'n_clicks'),
    [State('force-graph', 'selectedNodes'),
     State('direction-radio', 'value'),
     State('min-conn-input', 'value'),
     State('graph-nodes', 'data'),
     State('graph-links', 'data')],
    prevent_initial_call=True
)
def discover_neighbors(n_clicks, selected_nodes, direction, min_conn, current_nodes, current_links):
    if not n_clicks or not selected_nodes:
        raise PreventUpdate

    current_nodes = current_nodes or []
    current_links = current_links or []

    new_nodes, new_links = explorer.discover_neighbors(selected_nodes, min_conn, direction)

    existing_ids = {n['id'] for n in current_nodes}
    added_any = False
    for node in new_nodes:
        if node['id'] not in existing_ids:
            current_nodes.append(node)
            existing_ids.add(node['id'])
            added_any = True

    if added_any:
        explorer.hop_counter += 1

    # Add new links (avoid duplicates)
    existing_links = {(l['source'], l['target']) for l in current_links}
    for link in new_links:
        key = (link['source'], link['target'])
        if key not in existing_links:
            current_links.append(link)
            existing_links.add(key)

    # Re-output the seed selection so it survives the graph update
    return current_nodes, current_links, selected_nodes


# Delete selected nodes
@app.callback(
    [Output('graph-nodes', 'data', allow_duplicate=True),
     Output('graph-links', 'data', allow_duplicate=True),
     Output('force-graph', 'selectedNodes')],
    Input('delete-btn', 'n_clicks'),
    [State('force-graph', 'selectedNodes'),
     State('graph-nodes', 'data'),
     State('graph-links', 'data')],
    prevent_initial_call=True
)
def delete_selected(n_clicks, selected_nodes, current_nodes, current_links):
    if not n_clicks or not selected_nodes:
        raise PreventUpdate

    selected_set = set(selected_nodes)
    current_nodes = current_nodes or []
    current_links = current_links or []

    # Remove selected nodes
    new_nodes = [n for n in current_nodes if n['id'] not in selected_set]

    # Remove links connected to deleted nodes
    new_links = [
        l for l in current_links
        if l['source'] not in selected_set and l['target'] not in selected_set
    ]

    return new_nodes, new_links, []


# Export functionality
@app.callback(
    Output('export-download', 'data'),
    Input({'type': 'export-btn', 'index': ALL}, 'n_clicks'),
    [State('graph-nodes', 'data'),
     State('graph-links', 'data'),
     State('legend-labels', 'data')],
    prevent_initial_call=True
)
def export_graph(n_clicks_list, nodes, links, legend_labels):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate

    prop_id = ctx.triggered[0]['prop_id']
    clicked_id = json.loads(prop_id.rsplit('.', 1)[0])
    fmt = clicked_id['index']

    nodes = nodes or []
    links = links or []
    legend_labels = legend_labels or {}

    if not nodes:
        raise PreventUpdate

    def hop_label(hop):
        default = 'seed' if hop == 0 else f'hop {hop}'
        return legend_labels.get(str(hop), default)

    if fmt == 'csv-nodes':
        lines = ['domain,type,hop,hop_label,connections']
        for n in nodes:
            hop = n.get('hop', 0)
            lines.append(f"{n['id']},{n.get('type','')},{hop},{hop_label(hop)},{n.get('connections','')}")
        return dict(content='\n'.join(lines), filename='nodes.csv')

    elif fmt == 'csv-edges':
        lines = ['source,target']
        for l in links:
            lines.append(f"{l['source']},{l['target']}")
        return dict(content='\n'.join(lines), filename='edges.csv')

    elif fmt == 'gexf':
        root = ET.Element('gexf', xmlns='http://www.gexf.net/1.2draft', version='1.2')
        graph_el = ET.SubElement(root, 'graph', defaultedgetype='directed')

        attrs = ET.SubElement(graph_el, 'attributes', {'class': 'node'})
        ET.SubElement(attrs, 'attribute', id='0', title='type', type='string')
        ET.SubElement(attrs, 'attribute', id='1', title='hop', type='integer')
        ET.SubElement(attrs, 'attribute', id='2', title='connections', type='integer')
        ET.SubElement(attrs, 'attribute', id='3', title='hop_label', type='string')

        nodes_el = ET.SubElement(graph_el, 'nodes')
        for n in nodes:
            hop = n.get('hop', 0)
            node_el = ET.SubElement(nodes_el, 'node', id=n['id'], label=n.get('label', n['id']))
            av = ET.SubElement(node_el, 'attvalues')
            ET.SubElement(av, 'attvalue', {'for': '0', 'value': str(n.get('type', ''))})
            ET.SubElement(av, 'attvalue', {'for': '1', 'value': str(hop)})
            ET.SubElement(av, 'attvalue', {'for': '2', 'value': str(n.get('connections', ''))})
            ET.SubElement(av, 'attvalue', {'for': '3', 'value': hop_label(hop)})

        edges_el = ET.SubElement(graph_el, 'edges')
        for i, l in enumerate(links):
            ET.SubElement(edges_el, 'edge', id=str(i), source=l['source'], target=l['target'])

        buf = io.StringIO()
        tree = ET.ElementTree(root)
        tree.write(buf, encoding='unicode', xml_declaration=True)
        return dict(content=buf.getvalue(), filename='graph.gexf')

    raise PreventUpdate


# URL change triggers example loading (with confirmation if data exists)
@app.callback(
    [Output('example-confirm', 'displayed'),
     Output('example-confirm', 'message'),
     Output('pending-example', 'data'),
     Output('example-loading', 'data', allow_duplicate=True)],
    Input('url', 'pathname'),
    State('graph-nodes', 'data'),
    prevent_initial_call='initial_duplicate'
)
def url_to_example(pathname, current_nodes):
    if not pathname or pathname == '/':
        raise PreventUpdate
    example_type = EXAMPLE_MAP.get(pathname)
    if not example_type:
        raise PreventUpdate

    name = EXAMPLE_NAMES.get(example_type, example_type)
    has_data = current_nodes and len(current_nodes) > 0

    if has_data:
        # Show confirmation, store pending example, don't load yet
        return True, f"Loading '{name}' will replace the current graph. Continue?", example_type, dash.no_update
    # No existing data, load directly
    return False, '', None, example_type


# Confirmation triggers loading from pending example
@app.callback(
    Output('example-loading', 'data', allow_duplicate=True),
    Input('example-confirm', 'submit_n_clicks'),
    State('pending-example', 'data'),
    prevent_initial_call=True
)
def confirm_example_load(submit_clicks, pending):
    if submit_clicks and pending:
        return pending
    raise PreventUpdate


# Load example graph from example-loading store
@app.callback(
    [Output('graph-nodes', 'data', allow_duplicate=True),
     Output('graph-links', 'data', allow_duplicate=True),
     Output('legend-labels', 'data', allow_duplicate=True)],
    Input('example-loading', 'data'),
    prevent_initial_call=True
)
def load_example_graph(example_type):
    if not example_type:
        raise PreventUpdate

    # Map example type to pickle file
    pickle_files = {
        'iranian': 'iranian_news_network.pkl',
        'high-profile': 'high_profile_news_network.pkl',
        'link-spam': 'link_spam.pkl',
        'pravda': 'pravda_network.pkl',
        'think-tanks': 'think_tanks.pkl',
    }

    pickle_file = pickle_files.get(example_type)
    if not pickle_file:
        raise PreventUpdate

    pickle_path = PICKLE_DIR / pickle_file

    try:
        # Load precomputed graph from pickle
        with open(pickle_path, 'rb') as f:
            G = pickle.load(f)

        # Prune isolates (nodes with no edges) before converting
        isolates = list(nx.isolates(G))
        G.remove_nodes_from(isolates)

        # Build node_type → hop mapping. Seeds are always hop 0; each distinct
        # non-seed node_type gets the next available hop number so it gets its
        # own color and legend entry.
        type_to_hop = {'seed': 0}
        legend_labels = {'0': 'seed'}
        next_hop = 1
        for _, data in G.nodes(data=True):
            if not data.get('is_seed'):
                ntype = data.get('node_type', 'discovered')
                if ntype not in type_to_hop:
                    type_to_hop[ntype] = next_hop
                    legend_labels[str(next_hop)] = ntype
                    next_hop += 1

        # Calculate in-degree and out-degree for connection counts
        in_degree = dict(G.in_degree())
        out_degree = dict(G.out_degree())

        # Convert NetworkX to nodes/links
        nodes = []
        links = []

        for node, data in G.nodes(data=True):
            node_type = data.get('node_type', 'seed')

            if 'total_connections' in data:
                connections = data['total_connections']
            elif 'connections' in data:
                connections = data['connections']
            elif data.get('is_seed'):
                connections = in_degree.get(node, 0)
            else:
                connections = out_degree.get(node, 0)

            if data.get('is_seed'):
                node_hop = 0
            else:
                node_hop = type_to_hop.get(node_type, 1)

            nodes.append({
                'id': node,
                'label': node,
                'type': node_type,
                'hop': node_hop,
                'connections': connections,
            })

        for src, tgt, _ in G.edges(data=True):
            links.append({'source': src, 'target': tgt})

        return nodes, links, legend_labels

    except Exception as e:
        print(f"Error loading example from {pickle_path}: {e}")
        raise PreventUpdate


# Clientside callback to set graph dimensions
app.clientside_callback(
    """
    function(trigger) {
        var container = document.getElementById('graph-container');
        if (container) {
            var rect = container.getBoundingClientRect();
            return [Math.floor(rect.width), Math.floor(rect.height)];
        }
        return [800, 600];
    }
    """,
    [Output('force-graph', 'width'),
     Output('force-graph', 'height')],
    Input('graph-nodes', 'data'),
)


server = app.server


# Serve app for example URL paths (enables direct URL navigation)
@server.route('/link-spam-network')
@server.route('/high-profile-news-network')
@server.route('/iranian-news-network')
def serve_example_routes():
    return app.index()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    # use_reloader=False prevents double webgraph loading in debug mode
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=port) #, dev_tools_ui=False, dev_tools_props_check=False)
