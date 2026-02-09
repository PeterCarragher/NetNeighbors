"""Simple test app for dash_force_graph component."""

from dash import Dash, html, dcc, Input, Output, State
from dash_force_graph import ForceGraph

app = Dash(__name__)

# Sample graph data
nodes = [
    {'id': 'cnn.com', 'label': 'cnn.com', 'type': 'seed', 'connections': 0},
    {'id': 'bbc.com', 'label': 'bbc.com', 'type': 'seed', 'connections': 0},
    {'id': 'nytimes.com', 'label': 'nytimes.com', 'type': 'seed', 'connections': 0},
    {'id': 'spammer1.com', 'label': 'spammer1.com', 'type': 'discovered', 'connections': 3},
    {'id': 'spammer2.com', 'label': 'spammer2.com', 'type': 'discovered', 'connections': 2},
    {'id': 'news-site.com', 'label': 'news-site.com', 'type': 'discovered', 'connections': 2},
]

links = [
    {'source': 'spammer1.com', 'target': 'cnn.com'},
    {'source': 'spammer1.com', 'target': 'bbc.com'},
    {'source': 'spammer1.com', 'target': 'nytimes.com'},
    {'source': 'spammer2.com', 'target': 'cnn.com'},
    {'source': 'spammer2.com', 'target': 'bbc.com'},
    {'source': 'news-site.com', 'target': 'cnn.com'},
    {'source': 'news-site.com', 'target': 'nytimes.com'},
]

app.layout = html.Div([
    html.H1("Force Graph Test"),
    html.Div([
        html.Div([
            ForceGraph(
                id='graph',
                nodes=nodes,
                links=links,
                width=800,
                height=600,
                selectedNodes=[],
            ),
        ], style={'flex': '1'}),
        html.Div([
            html.H3("Selection"),
            html.Div(id='selection-output', style={'fontFamily': 'monospace'}),
            html.H3("Right Click"),
            html.Div(id='right-click-output', style={'fontFamily': 'monospace'}),
            html.H3("Actions"),
            dcc.Input(id='center-input', placeholder='Node ID to center on'),
            html.Button('Center', id='center-btn', n_clicks=0),
        ], style={'width': '300px', 'padding': '20px'}),
    ], style={'display': 'flex'}),
])


@app.callback(
    Output('selection-output', 'children'),
    Input('graph', 'selectedNodes')
)
def display_selection(selected):
    if not selected:
        return "No nodes selected"
    return html.Ul([html.Li(node) for node in selected])


@app.callback(
    Output('right-click-output', 'children'),
    [Input('graph', 'rightClickedNode'),
     Input('graph', 'rightClickPosition')]
)
def display_right_click(node, pos):
    if not node:
        return "Right-click a node"
    return f"Node: {node}, Position: {pos}"


@app.callback(
    Output('graph', 'centerAt'),
    Input('center-btn', 'n_clicks'),
    State('center-input', 'value'),
    prevent_initial_call=True
)
def center_on_node(n_clicks, node_id):
    return node_id


if __name__ == '__main__':
    app.run(debug=True, port=8051)
