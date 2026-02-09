# Dash Force Graph

A high-performance Dash component for graph visualization using [force-graph](https://github.com/vasturiano/force-graph).

## Features

- **WebGL rendering** - Handles 10K+ nodes smoothly
- **Interactive** - Pan, zoom, node selection, drag
- **Dash integration** - Two-way binding for selections and callbacks
- **Customizable** - Node colors, sizes, labels, link styling

## Installation

### Build from source

```bash
# Install npm dependencies and build JavaScript bundle
npm install
npm run build

# Install Python package
pip install -e .
```

## Usage

```python
from dash import Dash, html, Input, Output
from dash_force_graph import ForceGraph

app = Dash(__name__)

nodes = [
    {'id': 'node1', 'label': 'Node 1', 'color': '#ff6b6b'},
    {'id': 'node2', 'label': 'Node 2', 'color': '#4ecdc4'},
    {'id': 'node3', 'label': 'Node 3', 'color': '#4ecdc4'},
]

links = [
    {'source': 'node1', 'target': 'node2'},
    {'source': 'node2', 'target': 'node3'},
]

app.layout = html.Div([
    ForceGraph(
        id='graph',
        nodes=nodes,
        links=links,
        width=800,
        height=600,
        selectedNodes=[],
    ),
    html.Div(id='selection-output')
])

@app.callback(
    Output('selection-output', 'children'),
    Input('graph', 'selectedNodes')
)
def display_selection(selected):
    return f"Selected: {selected}"

if __name__ == '__main__':
    app.run(debug=True)
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| id | string | - | Component ID |
| nodes | array | [] | List of node objects with at least `id` |
| links | array | [] | List of link objects with `source` and `target` |
| selectedNodes | array | [] | Currently selected node IDs (two-way binding) |
| width | number | - | Container width in pixels |
| height | number | - | Container height in pixels |
| enableZoom | bool | true | Enable zoom interaction |
| enablePan | bool | true | Enable pan interaction |
| enableNodeDrag | bool | true | Enable node dragging |
| centerAt | string | - | Node ID to center view on |
| zoomLevel | number | - | Zoom level |

## Node Object

```javascript
{
    id: 'unique-id',      // Required
    label: 'Display Name', // Optional, defaults to id
    color: '#ff6b6b',      // Optional
    type: 'seed',          // Optional, affects default color
    connections: 10,       // Optional, affects node size
}
```

## Link Object

```javascript
{
    source: 'node1-id',  // Required
    target: 'node2-id',  // Required
}
```
