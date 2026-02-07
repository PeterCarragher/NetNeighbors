"""
NetNeighbors Graph Explorer with Dash Cytoscape
Full integration with Common Crawl webgraph discovery
"""

import os
import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_cytoscape as cyto
import json

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
app = dash.Dash(__name__)

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

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🕸️ NetNeighbors: Common Crawl Graph Explorer"),
        html.P("Interactive multi-hop domain discovery using the Common Crawl webgraph")
    ], style={
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'color': 'white',
        'padding': '30px',
        'margin-bottom': '20px',
        'border-radius': '10px'
    }),
    
    html.Div([
        # Left panel - Controls
        html.Div([
            # Initial query section
            html.Div([
                html.H3("🎯 Initial Query", style={'margin-bottom': '15px'}),
                
                dcc.Textarea(
                    id='seed-domains-input',
                    placeholder='Enter seed domains (one per line):\ncnn.com\nbbc.com\nfoxnews.com',
                    style={
                        'width': '100%',
                        'height': '120px',
                        'padding': '10px',
                        'border': '1px solid #ddd',
                        'border-radius': '5px',
                        'font-family': 'monospace',
                        'font-size': '12px'
                    }
                ),
                
                html.Div([
                    html.Label("Min Connections:", style={'font-weight': 'bold', 'margin-top': '10px'}),
                    dcc.Slider(
                        id='min-connections-slider',
                        min=1,
                        max=50,
                        step=1,
                        value=5,
                        marks={1: '1', 10: '10', 25: '25', 50: '50'},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], style={'margin': '15px 0'}),
                
                html.Div([
                    html.Label("Direction:", style={'font-weight': 'bold'}),
                    dcc.RadioItems(
                        id='direction-radio',
                        options=[
                            {'label': ' Backlinks (who links to seeds)', 'value': 'backlinks'},
                            {'label': ' Outlinks (who seeds link to)', 'value': 'outlinks'}
                        ],
                        value='backlinks',
                        style={'margin-top': '5px'}
                    )
                ], style={'margin': '15px 0'}),
                
                html.Button(
                    '🚀 Discover Domains',
                    id='discover-btn',
                    n_clicks=0,
                    style={
                        'width': '100%',
                        'padding': '12px',
                        'background': '#667eea',
                        'color': 'white',
                        'border': 'none',
                        'border-radius': '5px',
                        'cursor': 'pointer',
                        'font-size': '15px',
                        'font-weight': 'bold',
                        'margin-top': '10px'
                    }
                )
            ], style={
                'background': 'white',
                'padding': '20px',
                'border-radius': '8px',
                'margin-bottom': '20px',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
            }),
            
            # Graph operations section
            html.Div([
                html.H3("🔧 Graph Operations", style={'margin-bottom': '15px'}),
                
                html.Button(
                    '➕ Expand Selected',
                    id='expand-btn',
                    n_clicks=0,
                    style={
                        'width': '100%',
                        'padding': '10px',
                        'margin': '5px 0',
                        'background': '#4ecdc4',
                        'color': 'white',
                        'border': 'none',
                        'border-radius': '5px',
                        'cursor': 'pointer',
                        'font-size': '14px'
                    }
                ),
                
                html.Div([
                    html.Button(
                        'Select Seeds',
                        id='select-seeds-btn',
                        n_clicks=0,
                        style={
                            'width': '48%',
                            'padding': '8px',
                            'margin': '5px 1%',
                            'background': '#95a5a6',
                            'color': 'white',
                            'border': 'none',
                            'border-radius': '5px',
                            'cursor': 'pointer',
                            'font-size': '12px'
                        }
                    ),
                    html.Button(
                        'Select Hop 1',
                        id='select-hop1-btn',
                        n_clicks=0,
                        style={
                            'width': '48%',
                            'padding': '8px',
                            'margin': '5px 1%',
                            'background': '#95a5a6',
                            'color': 'white',
                            'border': 'none',
                            'border-radius': '5px',
                            'cursor': 'pointer',
                            'font-size': '12px'
                        }
                    )
                ], style={'display': 'flex', 'flex-wrap': 'wrap'}),
                
                html.Button(
                    '🗑️ Delete Selected',
                    id='delete-btn',
                    n_clicks=0,
                    style={
                        'width': '100%',
                        'padding': '10px',
                        'margin': '5px 0',
                        'background': '#e74c3c',
                        'color': 'white',
                        'border': 'none',
                        'border-radius': '5px',
                        'cursor': 'pointer',
                        'font-size': '14px'
                    }
                ),
                
                html.Button(
                    '🔄 Clear Graph',
                    id='reset-btn',
                    n_clicks=0,
                    style={
                        'width': '100%',
                        'padding': '10px',
                        'margin': '5px 0',
                        'background': '#95a5a6',
                        'color': 'white',
                        'border': 'none',
                        'border-radius': '5px',
                        'cursor': 'pointer',
                        'font-size': '14px'
                    }
                )
            ], style={
                'background': 'white',
                'padding': '20px',
                'border-radius': '8px',
                'margin-bottom': '20px',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
            }),
            
            # Stats section
            html.Div([
                html.H3("📊 Graph Stats", style={'margin-bottom': '15px'}),
                html.Div(id='graph-stats', style={'font-size': '14px'})
            ], style={
                'background': 'white',
                'padding': '20px',
                'border-radius': '8px',
                'margin-bottom': '20px',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
            }),
            
            # Selection info section
            html.Div([
                html.H3("✓ Selection", style={'margin-bottom': '15px'}),
                html.Div(id='selection-info', style={
                    'font-size': '12px',
                    'max-height': '250px',
                    'overflow-y': 'auto'
                })
            ], style={
                'background': 'white',
                'padding': '20px',
                'border-radius': '8px',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
            
        ], style={'width': '350px', 'padding': '0 20px'}),
        
        # Right panel - Graph
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
                style={'width': '100%', 'height': '800px', 'background': '#f8f9fa', 'border-radius': '8px'},
                elements=[],
                stylesheet=stylesheet,
                boxSelectionEnabled=True,
                autoungrabify=False,
                userZoomingEnabled=True,
                userPanningEnabled=True
            )
        ], style={'flex': 1, 'padding': '0 20px'})
        
    ], style={'display': 'flex'}),
    
    # Hidden stores
    dcc.Store(id='graph-state', data={'hop_count': 0, 'initialized': False}),
    dcc.Store(id='query-log', data=[])
])


@app.callback(
    [Output('cytoscape-graph', 'elements'),
     Output('graph-state', 'data'),
     Output('query-log', 'data')],
    [Input('discover-btn', 'n_clicks'),
     Input('expand-btn', 'n_clicks'),
     Input('delete-btn', 'n_clicks'),
     Input('reset-btn', 'n_clicks'),
     Input('select-seeds-btn', 'n_clicks'),
     Input('select-hop1-btn', 'n_clicks')],
    [State('seed-domains-input', 'value'),
     State('min-connections-slider', 'value'),
     State('direction-radio', 'value'),
     State('cytoscape-graph', 'selectedNodeData'),
     State('cytoscape-graph', 'elements'),
     State('graph-state', 'data'),
     State('query-log', 'data')]
)
def update_graph(discover_clicks, expand_clicks, delete_clicks, reset_clicks,
                select_seeds_clicks, select_hop1_clicks,
                seed_input, min_connections, direction, selected_nodes,
                current_elements, state, query_log):
    """Main callback for all graph operations"""
    
    ctx = callback_context
    if not ctx.triggered:
        return current_elements, state, query_log
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Reset graph
    if button_id == 'reset-btn':
        explorer.hop_counter = 0
        return [], {'hop_count': 0, 'initialized': False}, []
    
    # Initial discovery
    if button_id == 'discover-btn':
        if not seed_input or not seed_input.strip():
            return current_elements, state, query_log
        
        # Parse seed domains
        seeds = [d.strip() for d in seed_input.split('\n') if d.strip()]
        
        # Create seed nodes
        seed_nodes = [
            {
                'data': {
                    'id': domain,
                    'label': domain,
                    'type': 'seed',
                    'hop': 0
                },
                'classes': 'seed'
            }
            for domain in seeds
        ]
        
        # Discover connected domains
        discovered_nodes, edges = explorer.discover_neighbors(seeds, min_connections, direction)
        
        # Combine elements
        new_elements = seed_nodes + discovered_nodes + edges
        
        # Update state
        state['hop_count'] = 1
        state['initialized'] = True
        
        # Log query
        query_log.append({
            'action': 'discover',
            'seeds': seeds,
            'min_connections': min_connections,
            'direction': direction,
            'results': len(discovered_nodes)
        })
        
        return new_elements, state, query_log
    
    # Expand selected nodes
    if button_id == 'expand-btn':
        if not selected_nodes:
            return current_elements, state, query_log
        
        # Get selected domain names
        selected_domains = [node['id'] for node in selected_nodes]
        
        # Discover neighbors
        new_nodes, new_edges = explorer.discover_neighbors(
            selected_domains, min_connections, direction
        )
        
        # Get existing node IDs to avoid duplicates
        existing_ids = {
            elem['data']['id'] 
            for elem in current_elements 
            if 'source' not in elem['data']
        }
        
        # Filter duplicates
        unique_nodes = [
            node for node in new_nodes 
            if node['data']['id'] not in existing_ids
        ]
        
        # Add to graph
        updated_elements = current_elements + unique_nodes + new_edges
        
        # Update state
        state['hop_count'] = state.get('hop_count', 1) + 1
        
        # Log query
        query_log.append({
            'action': 'expand',
            'seeds': selected_domains,
            'min_connections': min_connections,
            'direction': direction,
            'results': len(unique_nodes)
        })
        
        return updated_elements, state, query_log
    
    # Delete selected nodes
    if button_id == 'delete-btn':
        if not selected_nodes:
            return current_elements, state, query_log
        
        selected_ids = {node['id'] for node in selected_nodes}
        
        # Remove selected nodes and connected edges
        filtered_elements = [
            elem for elem in current_elements
            if (
                ('source' not in elem['data'] and elem['data']['id'] not in selected_ids) or
                ('source' in elem['data'] and 
                 elem['data']['source'] not in selected_ids and 
                 elem['data']['target'] not in selected_ids)
            )
        ]
        
        return filtered_elements, state, query_log
    
    # Selection helpers (these will trigger selection in the UI)
    # Note: Direct node selection via callbacks requires a different approach
    # For now, these are placeholders - selection will be manual
    
    return current_elements, state, query_log


@app.callback(
    Output('selection-info', 'children'),
    Input('cytoscape-graph', 'selectedNodeData')
)
def display_selection(selected_nodes):
    """Display selected nodes information"""
    if not selected_nodes:
        return html.Div(
            "No nodes selected. Click nodes to select.",
            style={'color': '#999', 'font-style': 'italic'}
        )
    
    return html.Div([
        html.Div(
            f"Selected: {len(selected_nodes)} node(s)",
            style={'font-weight': 'bold', 'margin-bottom': '10px'}
        ),
        html.Div([
            html.Div([
                html.Div(node['label'], style={'font-weight': '500'}),
                html.Div(
                    f"{node.get('type', 'unknown')} • {node.get('connections', 'N/A')} connections",
                    style={'font-size': '10px', 'color': '#666'}
                )
            ], style={
                'padding': '8px',
                'background': '#f0f0f0',
                'margin': '5px 0',
                'border-radius': '4px',
                'border-left': '3px solid #4ecdc4'
            })
            for node in selected_nodes
        ])
    ])


@app.callback(
    Output('graph-stats', 'children'),
    Input('cytoscape-graph', 'elements')
)
def update_stats(elements):
    """Update graph statistics"""
    if not elements:
        return html.Div("No graph data", style={'color': '#999', 'font-style': 'italic'})
    
    nodes = [e for e in elements if 'source' not in e['data']]
    edges = [e for e in elements if 'source' in e['data']]
    
    # Count by type
    seeds = len([n for n in nodes if n.get('classes') == 'seed'])
    discovered = len(nodes) - seeds
    
    return html.Div([
        html.Div([
            html.Span("Total Nodes: ", style={'color': '#666'}),
            html.Span(str(len(nodes)), style={'font-weight': 'bold'})
        ], style={'margin': '5px 0'}),
        html.Div([
            html.Span("├─ Seeds: ", style={'color': '#666'}),
            html.Span(str(seeds), style={'font-weight': 'bold', 'color': '#ff6b6b'})
        ], style={'margin': '5px 0'}),
        html.Div([
            html.Span("└─ Discovered: ", style={'color': '#666'}),
            html.Span(str(discovered), style={'font-weight': 'bold', 'color': '#4ecdc4'})
        ], style={'margin': '5px 0'}),
        html.Div([
            html.Span("Edges: ", style={'color': '#666'}),
            html.Span(str(len(edges)), style={'font-weight': 'bold'})
        ], style={'margin': '10px 0 5px 0'})
    ])


if __name__ == '__main__':
    app.run(debug=True, port=8050)