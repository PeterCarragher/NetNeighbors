# Interactive CommonCrawl Webgraph Demo
[![Live Demo](https://img.shields.io/badge/Live-Demo-blue?style=for-the-badge)](https://netneighbor.petercarragher.com/)

Discover related domains using link webgraph topology analysis. 

Given a list of seed domains, discovers other domains that are connected via backlinks or outlinks in the CommonCrawl web graph.

## Setup Instructions

```bash
pip install pyccwebgraph
```

If you are interested in general network analysis, checkout the [pyccwebgraph package](https://pypi.org/project/pyccwebgraph/). 

There is also a [separate repository for a colab notebook](https://github.com/PeterCarragher/NetNeighborsColab) that you can use to self host an instance of this demo.

## Discovery Interface
```bash
WEBGRAPH_DIR=/content/webgraphs/ WEBGRAPH_VERSION=cc-main-2024-feb-apr-may python discovery_network_vis.py
```

---

## Citation & References

If you use this notebook or the discovery interface in your research, please cite:

```bibtex
@article{carragher2024detection,
  title={Detection and Discovery of Misinformation Sources using Attributed Webgraphs},
  author={Carragher, Peter and Williams, Evan M and Carley, Kathleen M},
  journal={Proceedings of the International AAAI Conference on Web and Social Media},
  volume={18},
  pages={218--229},
  year={2024},
  url={https://arxiv.org/abs/2401.02379}
}

@article{carragher2025misinformation,
  title={Misinformation Resilient Search Rankings with Attributed Webgraphs},
  author={Carragher, Peter and Williams, Evan M and Spezzano, Francesca and Carley, Kathleen M},
  journal={ACM Transactions on Intelligent Systems and Technology},
  year={2025},
  url={https://dl.acm.org/doi/pdf/10.1145/3670410}
}
```

**Links:**
- GitHub Repository: https://github.com/CASOS-IDeaS-CMU/Detection-and-Discovery-of-Misinformation-Sources
- CommonCrawl Webgraphs: https://commoncrawl.org/web-graphs
- cc-webgraph Tools: https://github.com/commoncrawl/cc-webgraph

**Acknowledgments:** This demo uses the CommonCrawl web graph dataset and the WebGraph framework developed by Sebastiano Vigna and Paolo Boldi.
