# 🔍 News Source Discovery Using CommonCrawl Webgraph
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PeterCarragher/NetNeighborsColab/blob/master/discovery_notebook.ipynb)

Discover related domains using link topology analysis from the CommonCrawl web graph.

**Based on:**
- Carragher, P., Williams, E. M., & Carley, K. M. (2024). *Detection and Discovery of Misinformation Sources using Attributed Webgraphs*. ICWSM 2024. [Paper](https://arxiv.org/abs/2401.02379)
- Carragher, P., Williams, E. M., Spezzano, F., & Carley, K. M. (2025). *Misinformation Resilient Search Rankings with Attributed Webgraphs*. ACM TIST.

**Dataset:**
- CommonCrawl webgraph (Nov-Dec 2024, Jan 2025)
- 93.9M domains, 1.6B edges
- Domain-level aggregation

**What this notebook does:**
Given a list of seed domains, discovers other domains that are connected via backlinks or outlinks in the CommonCrawl web graph.

## 📋 Setup Instructions

**⏱️ Time: ~15 minutes (first time only)**

### Step 1: Enable High-RAM Runtime (REQUIRED)

1. Click **Runtime** → **Change runtime type**
2. Set **Runtime shape** to **High-RAM** ⚠️
3. Set **Hardware accelerator** to **GPU** (optional, for faster processing)
4. Click **Save**

*Why? The CommonCrawl webgraph requires >40GB RAM to process.*

### Step 2: (Optional) Mount Google Drive

**Recommended!** This caches the ~23GB webgraph so you don't re-download it every session.

Run the "Mount Google Drive" cell below and follow the prompts.

### Step 3: Run Setup Cells (One-Time)

**▶️ Click Run on each setup cell in order:**

1. **Check Available RAM** - Verifies you have enough memory
2. **Mount Google Drive** - (Optional) For persistent caching
3. **Install Java 17** - Required for WebGraph (~2 min)
4. **Download cc-webgraph Tools** - Clones and builds tools (~2 min)
5. **Download CommonCrawl Webgraph** - Downloads pre-built graph files (~10 min for 23GB)
6. **Verify Installation** - Confirms everything is ready

**Note:** Graph files are pre-built by CommonCrawl - no build step needed!

### Step 4: Use the Discovery Form

Scroll down to **Section 3: Discovery Interface** and interact with the form!

---

## 📚 Citation & References

If you use this notebook in your research, please cite:

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
  year={2025}
}
```

**Links:**
- Paper (ICWSM 2024): https://arxiv.org/abs/2401.02379
- GitHub Repository: https://github.com/CASOS-IDeaS-CMU/Detection-and-Discovery-of-Misinformation-Sources
- CommonCrawl Webgraphs: https://commoncrawl.org/web-graphs
- cc-webgraph Tools: https://github.com/commoncrawl/cc-webgraph

**Contact:**
- Peter Carragher: pcarragh@andrew.cmu.edu
- CASOS Lab: http://casos.cs.cmu.edu/

---

**License:** MIT

**Acknowledgments:** This notebook uses the CommonCrawl web graph dataset and the WebGraph framework developed by Sebastiano Vigna and Paolo Boldi.