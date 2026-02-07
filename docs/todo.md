* refactor: move
* multiple domains
* network visualizer, with multihop query ability: https://www.sigmajs.org/
* consider adding cc-webgraph as a git submodule instead of cloning it outside the repo in setup.sh. This would pin the version, simplify path resolution (no ../cc-webgraph guessing), and make the dependency explicit. Would require reworking paths in setup.sh, build_vertex_map.sh, graph_bridge.py (_detect_paths), and the Dockerfile.