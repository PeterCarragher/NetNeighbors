# Outer package init - re-export from inner package
# This file exists because the project directory shadows the installed package name
from dash_force_graph.dash_force_graph import ForceGraph
from dash_force_graph.dash_force_graph import __version__

# Override _js_dist with path relative to THIS directory (outer package)
# bundle.js is in dash_force_graph/bundle.js relative to here
_js_dist = [
    {
        'relative_package_path': 'dash_force_graph/bundle.js',
        'namespace': 'dash_force_graph',
    }
]

_css_dist = []

# Attach to component
ForceGraph._js_dist = _js_dist
ForceGraph._css_dist = _css_dist

__all__ = [
    'ForceGraph',
    '__version__',
    '_js_dist',
    '_css_dist',
]
