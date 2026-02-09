"""Dash Force Graph - High-performance graph visualization component."""

import os
import json

__version__ = '0.1.0'

# Get the path to this package
_current_path = os.path.dirname(os.path.abspath(__file__))

# Load metadata
_metadata_path = os.path.join(_current_path, 'metadata.json')
if os.path.exists(_metadata_path):
    with open(_metadata_path) as f:
        _metadata = json.load(f)
else:
    _metadata = {}

# JavaScript distribution - bundle.js is in this same directory
_js_dist = [
    {
        'relative_package_path': 'bundle.js',
        'namespace': 'dash_force_graph',
    }
]

_css_dist = []

from .ForceGraph import ForceGraph

# Attach dist info to the component
ForceGraph._js_dist = _js_dist
ForceGraph._css_dist = _css_dist

__all__ = [
    'ForceGraph',
    '__version__',
    '_js_dist',
    '_css_dist',
]
