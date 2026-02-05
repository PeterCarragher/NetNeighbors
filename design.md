# News Source Discovery Jupyter Notebook - Design Specification

**Project:** Misinformation Domain Discovery via Jupyter Notebook  
**Version:** 1.0  
**Date:** February 5, 2026  
**Target Platform:** Google Colab Pro (50GB+ RAM)

---

## Executive Summary

This notebook provides a **zero-installation** interface for researchers to discover related domains using CommonCrawl's webgraph data. Users simply click "Open in Colab," run the cells, and interact with a form to get results - no coding required.

**Key Features:**
- One-click setup via Google Colab
- Interactive form-based interface (no coding required)
- Uses CommonCrawl webgraph (93.9M domains, 1.6B edges)
- Leverages cc-webgraph Java tools (battle-tested)
- Results displayed as sortable table + CSV download
- Complete reproducibility for research

**Target Users:**
- Academic researchers
- Fact-checkers
- Journalists
- Misinformation analysts
- Anyone with a Colab Pro subscription

**Time Investment:**
- First-time setup: ~15 minutes (downloads 22.5GB)
- Subsequent runs: <2 minutes per query
- Data cached across sessions (persists in Google Drive)

---

## Table of Contents

1. [User Experience Overview](#1-user-experience-overview)
2. [Prerequisites](#2-prerequisites)
3. [Setup Instructions (User-Facing)](#3-setup-instructions-user-facing)
4. [Notebook Architecture](#4-notebook-architecture)
5. [Cell-by-Cell Breakdown](#5-cell-by-cell-breakdown)
6. [Technical Implementation](#6-technical-implementation)
7. [Error Handling](#7-error-handling)
8. [Output Format](#8-output-format)
9. [Limitations](#9-limitations)
10. [Future Enhancements](#10-future-enhancements)

---

## 1. User Experience Overview

### User Journey

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Click "Open in Colab" Badge in README      │
│         → Opens notebook in new browser tab         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: Enable GPU/High-RAM Runtime                 │
│         Runtime → Change runtime type → Python 3    │
│         Hardware accelerator → GPU (optional)       │
│         Runtime shape → High-RAM                    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: Run Setup Cells (One-Time, ~15 min)        │
│         - Installs Java 17                          │
│         - Downloads cc-webgraph tools               │
│         - Downloads CommonCrawl webgraph data       │
│         - Builds graph structures                   │
│         Status bar shows progress                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: Fill Out Discovery Form                    │
│         📝 Seed Domains: [textarea]                 │
│         🔢 Min Connections: [slider: 1-100]         │
│         ↔️  Direction: [radio: Backlinks/Outlinks]  │
│         🔘 [Run Discovery Button]                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 5: View Results (~30 sec - 2 min)             │
│         Progress: Processing 150 seed domains...    │
│         ✅ Found 847 candidate domains              │
│         📊 Interactive table (sortable, filterable) │
│         💾 [Download CSV] button                    │
└─────────────────────────────────────────────────────┘
```

### Visual Experience

**Before Running:**
```
╔════════════════════════════════════════════════════════╗
║  News Source Discovery Using CommonCrawl Webgraph     ║
║  Based on Carragher et al. (ICWSM 2024)               ║
╚════════════════════════════════════════════════════════╝

⚙️ Setup (Run Once)
[ ] Step 1: Install dependencies
[ ] Step 2: Download webgraph data (22.5GB)
[ ] Step 3: Build graph structures

📝 Discovery Form (Run Multiple Times)
[Disabled until setup complete]
```

**After Setup:**
```
╔════════════════════════════════════════════════════════╗
║  News Source Discovery Using CommonCrawl Webgraph     ║
║  Based on Carragher et al. (ICWSM 2024)               ║
╚════════════════════════════════════════════════════════╝

✅ Setup Complete
Graph loaded: 93,912,345 domains | 1,623,458,901 edges
Webgraph version: cc-main-2025-26-nov-dec-jan

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Discovery Configuration

Seed Domains (one per line):
┌────────────────────────────────────────────┐
│ example.com                                 │
│ test.org                                    │
│ sample.net                                  │
│                                             │
└────────────────────────────────────────────┘

Minimum Connections: [====○====] 5

Direction: ⦿ Backlinks (who links TO seeds)
           ○ Outlinks (who seeds link TO)

           [ Run Discovery ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Results

Processing... ████████████████████ 100%

Found 847 domains with ≥5 connections to seed list

  Domain               | Connections | Percentage
  ─────────────────────|─────────────|───────────
  discovered.com       |    45       |   15.0%
  related-site.org     |    38       |   12.7%
  another-domain.net   |    32       |   10.7%
  ...

           [ Download CSV ]
```

---

## 2. Prerequisites

### User Requirements

**Required:**
- Google account
- **Google Colab Pro** subscription ($9.99/month)
  - Provides 50GB+ RAM
  - Faster CPUs
  - Longer runtime (24 hours vs 12 hours)
  - Background execution

**Why Colab Pro is Required:**
- CommonCrawl webgraph: 22.5GB compressed, ~30GB in memory
- Free tier: 12-15GB RAM (insufficient)
- Pro tier: 52GB RAM (sufficient with headroom)
- Pro+ tier: 83GB RAM (even better)

**Optional but Recommended:**
- Mount Google Drive (to cache webgraph between sessions)
- GPU runtime (faster processing, but not required)

### Knowledge Requirements

**None!** The notebook is designed for non-programmers:
- No Python knowledge needed
- No Java knowledge needed
- No command-line experience needed
- Just: Click buttons, fill forms, read results

---

## 3. Setup Instructions (User-Facing)

These instructions appear at the top of the notebook in a prominent markdown cell:

### 📋 Setup Instructions

**⏱️ Time: ~15 minutes (first time only)**

#### Step 1: Enable High-RAM Runtime (Required)

1. Click **Runtime** → **Change runtime type**
2. Set **Runtime shape** to **High-RAM**
3. Set **Hardware accelerator** to **GPU** (optional, for faster processing)
4. Click **Save**

*Why? The CommonCrawl webgraph is 22.5GB and requires >40GB RAM to process.*

#### Step 2: (Optional) Mount Google Drive

**Recommended!** This caches the 22.5GB webgraph so you don't re-download it every session.

1. Run the "Mount Google Drive" cell below
2. Click the link and authorize access
3. Copy the authorization code
4. Paste into the input box

*Note: Webgraph will be saved to `My Drive/Colab_Data/webgraph/`*

#### Step 3: Run Setup Cells (One-Time)

**▶️ Click Run on each of the following cells in order:**

- **Cell: "Install Java & Dependencies"** (~2 minutes)
- **Cell: "Download cc-webgraph Tools"** (~1 minute)
- **Cell: "Download CommonCrawl Webgraph"** (~10 minutes for 22.5GB)
- **Cell: "Build Graph Structures"** (~2 minutes)

**Progress bars will show download status.**

⚠️ **Important:** Wait for each cell to complete before running the next.

#### Step 4: Verify Setup

Run the **"Verify Installation"** cell. You should see:
```
✅ Java installed: version 17.0.9
✅ cc-webgraph tools: found
✅ Webgraph data: 93,912,345 domains
✅ Graph structures: built
Ready to discover!
```

#### Step 5: Use the Discovery Form

Scroll down to **"Discovery Interface"** and:
1. Enter seed domains (one per line)
2. Adjust minimum connections slider
3. Select backlinks or outlinks
4. Click **Run Discovery**

Results appear in ~30 seconds to 2 minutes.

---

## 4. Notebook Architecture

### Logical Sections

The notebook is divided into clear sections:

```
┌─────────────────────────────────────────────────────┐
│ Section 1: Introduction & Citation                 │
│ - Title, authors, paper links                       │
│ - Brief methodology explanation                     │
│ - Setup instructions                                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Section 2: Setup (Run Once)                        │
│ - Cell: Mount Google Drive (optional)              │
│ - Cell: Install Java 17                            │
│ - Cell: Download cc-webgraph                       │
│ - Cell: Download webgraph data                     │
│ - Cell: Build graph structures                     │
│ - Cell: Verify installation                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Section 3: Helper Functions (Hidden)               │
│ - Load graph wrapper                                │
│ - Domain name conversion utilities                  │
│ - Discovery algorithm wrapper                       │
│ - Result formatting functions                       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Section 4: Discovery Interface (Interactive)       │
│ - Input widgets (textarea, slider, radio)          │
│ - Run button with callback                         │
│ - Progress indicators                               │
│ - Results display (table + download)               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Section 5: Advanced Usage (Optional)               │
│ - Batch processing multiple seed lists             │
│ - Custom filtering                                  │
│ - Direct Java/JShell access                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Section 6: Citation & References                   │
│ - BibTeX citation                                   │
│ - Link to papers                                    │
│ - Link to GitHub repository                        │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (Widgets)
      ↓
Python Validation
      ↓
Write seeds.txt
      ↓
Call Java Tool (cc-webgraph)
      ↓
Execute Discovery Algorithm
      ↓
Write results.csv
      ↓
Python reads CSV
      ↓
Display as Pandas DataFrame
      ↓
User downloads CSV
```

### File Structure in Colab

```
/content/                           # Colab working directory
├── cc-webgraph/                    # Cloned repository
│   ├── target/
│   │   └── cc-webgraph-*.jar       # Compiled tools
│   └── src/
├── webgraph/                       # Or /gdrive/MyDrive/Colab_Data/webgraph/
│   ├── cc-main-2025-26-domain-vertices.txt.gz
│   ├── cc-main-2025-26-domain-edges.txt.gz
│   ├── cc-main-2025-26-domain.graph
│   ├── cc-main-2025-26-domain.properties
│   └── cc-main-2025-26-domain-t.graph  # Transpose
├── seeds.txt                       # Temporary input file
├── results.csv                     # Output file
└── discovery_log.txt               # Execution log
```

---

## 5. Cell-by-Cell Breakdown

### Section 1: Introduction

#### Cell 1 (Markdown): Title & Overview
```markdown
# 🔍 News Source Discovery Using CommonCrawl Webgraph

Discover related domains using link topology analysis from the CommonCrawl web graph.

**Based on:**
- Carragher, P., Williams, E. M., & Carley, K. M. (2024). Detection and Discovery of 
  Misinformation Sources using Attributed Webgraphs. ICWSM 2024.
- Carragher, P., Williams, E. M., Spezzano, F., & Carley, K. M. (2025). 
  Misinformation Resilient Search Rankings with Attributed Webgraphs. ACM TIST.

**Dataset:**
- CommonCrawl webgraph (Nov-Dec 2024, Jan 2025)
- 93.9M domains, 1.6B edges
- Domain-level aggregation

**What this notebook does:**
Given a list of seed domains, discovers other domains that are connected via backlinks 
or outlinks in the CommonCrawl web graph.
```

#### Cell 2 (Markdown): Setup Instructions
```markdown
## 📋 Setup Instructions
[Full setup instructions from Section 3 above]
```

### Section 2: Setup (Run Once)

#### Cell 3 (Code): Check Colab Pro
```python
import psutil

# Check available RAM
ram_gb = psutil.virtual_memory().total / (1024**3)
print(f"Available RAM: {ram_gb:.1f} GB")

if ram_gb < 40:
    print("⚠️ WARNING: You need Colab Pro for this notebook!")
    print("   Required: 40GB+ RAM")
    print("   You have: {:.1f} GB".format(ram_gb))
    print("\n   Please upgrade to Colab Pro and enable High-RAM runtime:")
    print("   Runtime → Change runtime type → Runtime shape: High-RAM")
else:
    print("✅ Sufficient RAM available")
```

#### Cell 4 (Code): Mount Google Drive (Optional)
```python
from google.colab import drive

# Ask user if they want to mount Drive
mount = input("Mount Google Drive to cache webgraph? (yes/no): ").lower()

if mount == 'yes':
    drive.mount('/content/drive')
    WEBGRAPH_DIR = '/content/drive/MyDrive/Colab_Data/webgraph'
    print(f"✅ Webgraph will be cached in: {WEBGRAPH_DIR}")
else:
    WEBGRAPH_DIR = '/content/webgraph'
    print("⚠️ Webgraph will be downloaded each session (~15 min)")

# Create directory
!mkdir -p {WEBGRAPH_DIR}
```

#### Cell 5 (Code): Install Java 17
```python
%%bash
# Install Java 17 (required for cc-webgraph)
apt-get update -qq
apt-get install -y -qq openjdk-17-jdk-headless

# Verify installation
java -version
```

#### Cell 6 (Code): Download cc-webgraph
```python
%%bash
# Clone cc-webgraph repository
if [ ! -d "cc-webgraph" ]; then
    git clone https://github.com/commoncrawl/cc-webgraph.git
    cd cc-webgraph
    mvn clean package -DskipTests -q
    echo "✅ cc-webgraph built successfully"
else
    echo "✅ cc-webgraph already exists"
fi
```

#### Cell 7 (Code): Download Webgraph Data
```python
%%bash
# Download CommonCrawl webgraph (22.5GB)
VERSION="cc-main-2025-26-nov-dec-jan"
BASE_URL="https://data.commoncrawl.org/projects/hyperlinkgraph/$VERSION/domain"

cd $WEBGRAPH_DIR

# Check if already downloaded
if [ -f "${VERSION}-domain-vertices.txt.gz" ]; then
    echo "✅ Webgraph already downloaded"
    exit 0
fi

echo "Downloading webgraph data (22.5GB, ~10 minutes)..."

# Download vertices (domain list)
wget -q --show-progress \
    $BASE_URL/${VERSION}-domain-vertices.txt.gz

# Download edges (link structure)
wget -q --show-progress \
    $BASE_URL/${VERSION}-domain-edges.txt.gz

echo "✅ Download complete"
```

#### Cell 8 (Code): Build Graph Structures
```python
%%bash
# Build BVGraph structures for fast queries
cd /content/cc-webgraph

VERSION="cc-main-2025-26-nov-dec-jan"
VERTICES="$WEBGRAPH_DIR/${VERSION}-domain-vertices.txt.gz"
EDGES="$WEBGRAPH_DIR/${VERSION}-domain-edges.txt.gz"
OUTPUT="$WEBGRAPH_DIR/${VERSION}-domain"

# Build graph if not already built
if [ -f "${OUTPUT}.graph" ]; then
    echo "✅ Graph structures already built"
    exit 0
fi

echo "Building graph structures (~2 minutes)..."

./src/script/webgraph_ranking/process_webgraph.sh \
    preference_up \
    $VERTICES \
    $EDGES \
    $OUTPUT

echo "✅ Graph structures built"
```

#### Cell 9 (Code): Verify Installation
```python
import os
import subprocess

print("Verifying installation...\n")

# Check Java
result = subprocess.run(['java', '-version'], capture_output=True, text=True)
if result.returncode == 0:
    version = result.stderr.split('\n')[0]
    print(f"✅ Java: {version}")
else:
    print("❌ Java not found")

# Check cc-webgraph
jar_path = "/content/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar"
if os.path.exists(jar_path):
    print(f"✅ cc-webgraph: found")
else:
    print(f"❌ cc-webgraph: not found")

# Check webgraph data
version = "cc-main-2025-26-nov-dec-jan"
graph_file = f"{WEBGRAPH_DIR}/{version}-domain.graph"
vertices_file = f"{WEBGRAPH_DIR}/{version}-domain-vertices.txt.gz"

if os.path.exists(graph_file):
    # Count domains
    import gzip
    with gzip.open(vertices_file, 'rt') as f:
        num_domains = sum(1 for _ in f)
    print(f"✅ Webgraph: {num_domains:,} domains")
else:
    print("❌ Webgraph: not found")

print("\n" + "="*50)
print("🎉 Setup complete! Scroll down to use the discovery interface.")
print("="*50)
```

### Section 3: Helper Functions

#### Cell 10 (Code): Discovery Helper Class
```python
import subprocess
import pandas as pd
import os
from typing import List, Tuple

class WebgraphDiscovery:
    def __init__(self, webgraph_dir: str, version: str):
        self.webgraph_dir = webgraph_dir
        self.version = version
        self.jar_path = "/content/cc-webgraph/target/cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar"
        self.graph_base = f"{webgraph_dir}/{version}-domain"
        
    def discover(self, 
                 seed_domains: List[str], 
                 min_connections: int,
                 direction: str = 'backlinks') -> pd.DataFrame:
        """
        Run discovery algorithm.
        
        Args:
            seed_domains: List of seed domain names
            min_connections: Minimum number of connections required
            direction: 'backlinks' or 'outlinks'
            
        Returns:
            DataFrame with columns: domain, connections, percentage
        """
        # Write seeds to file
        with open('/content/seeds.txt', 'w') as f:
            for domain in seed_domains:
                f.write(domain.strip() + '\n')
        
        # Build Java command
        cmd = [
            'java',
            '-Xmx48g',  # Use 48GB heap (leave 4GB for OS)
            '-cp', self.jar_path,
            'org.commoncrawl.webgraph.DiscoveryTool',
            '--graph', self.graph_base,
            '--vertices', f"{self.webgraph_dir}/{self.version}-domain-vertices.txt.gz",
            '--seeds', '/content/seeds.txt',
            '--min-connections', str(min_connections),
            '--direction', direction,
            '--output', '/content/results.csv'
        ]
        
        # Execute
        print("Running discovery algorithm...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Discovery failed: {result.stderr}")
        
        # Read results
        if os.path.exists('/content/results.csv'):
            df = pd.read_csv('/content/results.csv')
            return df
        else:
            return pd.DataFrame(columns=['domain', 'connections', 'percentage'])
    
    def reverse_domain_notation(self, domain: str) -> str:
        """Convert example.com to com.example"""
        parts = domain.split('.')
        return '.'.join(reversed(parts))

# Initialize
discovery = WebgraphDiscovery(WEBGRAPH_DIR, "cc-main-2025-26-nov-dec-jan")
print("✅ Discovery tools initialized")
```

### Section 4: Discovery Interface

#### Cell 11 (Code): Interactive Form
```python
import ipywidgets as widgets
from IPython.display import display, HTML, FileLink
import pandas as pd

# Create widgets
domains_input = widgets.Textarea(
    value='',
    placeholder='Enter seed domains, one per line:\nexample.com\ntest.org\nsample.net',
    description='',
    layout=widgets.Layout(width='80%', height='200px'),
    style={'description_width': '0px'}
)

min_conn_slider = widgets.IntSlider(
    value=5,
    min=1,
    max=100,
    step=1,
    description='Min Connections:',
    style={'description_width': '150px'},
    layout=widgets.Layout(width='60%')
)

direction_radio = widgets.RadioButtons(
    options=[
        ('Backlinks (who links TO seeds)', 'backlinks'),
        ('Outlinks (who seeds link TO)', 'outlinks')
    ],
    value='backlinks',
    description='Direction:',
    style={'description_width': '150px'}
)

run_button = widgets.Button(
    description='🔍 Run Discovery',
    button_style='success',
    layout=widgets.Layout(width='200px', height='40px')
)

output_area = widgets.Output()

# Display form
display(HTML("<h2>📝 Discovery Configuration</h2>"))
display(HTML("<p><strong>Seed Domains</strong> (one per line):</p>"))
display(domains_input)
display(min_conn_slider)
display(direction_radio)
display(run_button)
display(output_area)

# Button callback
def on_run_click(b):
    output_area.clear_output()
    
    with output_area:
        # Validate input
        domains_text = domains_input.value.strip()
        if not domains_text:
            print("❌ Please enter at least one domain")
            return
        
        seed_domains = [d.strip() for d in domains_text.split('\n') if d.strip()]
        
        if len(seed_domains) == 0:
            print("❌ Please enter at least one domain")
            return
        
        if len(seed_domains) > 1000:
            print("❌ Maximum 1000 domains allowed")
            return
        
        print(f"Processing {len(seed_domains)} seed domains...")
        print(f"Direction: {direction_radio.value}")
        print(f"Minimum connections: {min_conn_slider.value}")
        print("\nThis may take 30 seconds to 2 minutes...\n")
        
        try:
            # Run discovery
            results_df = discovery.discover(
                seed_domains=seed_domains,
                min_connections=min_conn_slider.value,
                direction=direction_radio.value
            )
            
            # Display results
            if len(results_df) == 0:
                print("No domains found matching the criteria.")
                print("Try lowering the minimum connections threshold.")
            else:
                print(f"✅ Found {len(results_df)} domains\n")
                print("="*60)
                display(HTML("<h3>📊 Results</h3>"))
                
                # Style the dataframe
                styled_df = results_df.head(100).style.format({
                    'connections': '{:,.0f}',
                    'percentage': '{:.2f}%'
                }).background_gradient(subset=['connections'], cmap='YlOrRd')
                
                display(styled_df)
                
                if len(results_df) > 100:
                    print(f"\nShowing top 100 results. Full results available in CSV download.")
                
                # Download link
                print("\n" + "="*60)
                display(HTML("<h4>💾 Download Results</h4>"))
                display(FileLink('/content/results.csv', result_html_prefix="Click here to download: "))
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("\nIf the error persists, try restarting the runtime and re-running setup cells.")

run_button.on_click(on_run_click)
```

### Section 5: Advanced Usage (Optional)

#### Cell 12 (Code): Batch Processing
```python
# Hidden by default - for advanced users
```

### Section 6: Citation

#### Cell 13 (Markdown): Citation & References
```markdown
## 📚 Citation

If you use this notebook in your research, please cite:

```bibtex
@article{carragher2024detection,
  title={Detection and Discovery of Misinformation Sources using Attributed Webgraphs},
  author={Carragher, Peter and Williams, Evan M and Carley, Kathleen M},
  journal={Proceedings of the International AAAI Conference on Web and Social Media},
  volume={18},
  pages={218--229},
  year={2024}
}
```

**Links:**
- Paper: https://arxiv.org/abs/2401.02379
- GitHub: https://github.com/CASOS-IDeaS-CMU/Detection-and-Discovery-of-Misinformation-Sources
- CommonCrawl Webgraphs: https://commoncrawl.org/web-graphs
```

---

## 6. Technical Implementation

### Java Tool Integration

The notebook calls a Java class `DiscoveryTool` that wraps cc-webgraph functionality:

**File: `/content/cc-webgraph/src/main/java/org/commoncrawl/webgraph/DiscoveryTool.java`**

```java
package org.commoncrawl.webgraph;

// This would be a new class we add to cc-webgraph
// Or we use existing classes and call them via shell scripts

public class DiscoveryTool {
    public static void main(String[] args) {
        // Parse arguments
        // Load graph
        // Run discovery
        // Write results
    }
}
```

**Alternative:** Use shell scripts from cc-webgraph directly if they exist.

### Memory Management

**Java Heap:** 48GB (out of 52GB available)
```bash
java -Xmx48g -cp cc-webgraph.jar ...
```

**Why 48GB?**
- Webgraph in memory: ~30GB
- Working memory: ~15GB
- Leave 4GB for Python/OS

**Garbage Collection:**
```bash
-XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

### Performance Optimization

**Graph Loading:**
- Load once per session (cached in memory)
- Subsequent queries are fast (<30 seconds)

**Batching:**
- Process all seed domains in single Java invocation
- No need to restart Java process for each query

---

## 7. Error Handling

### Common Errors and Solutions

#### Error: OutOfMemoryError
**Cause:** Not using High-RAM runtime  
**Solution:** Runtime → Change runtime type → High-RAM

#### Error: Webgraph files not found
**Cause:** Download incomplete or Google Drive disconnected  
**Solution:** Re-run download cell

#### Error: Java not found
**Cause:** Java installation failed  
**Solution:** Re-run Java installation cell

#### Error: No domains found
**Cause:** Seeds not in webgraph or threshold too high  
**Solution:** Lower minimum connections threshold

### Error Display in Notebook

```python
try:
    results = discovery.discover(...)
except FileNotFoundError as e:
    print("❌ Setup incomplete. Please run all setup cells first.")
except subprocess.TimeoutExpired:
    print("❌ Discovery timed out. Try fewer seed domains.")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\n📝 Troubleshooting:")
    print("1. Check that all setup cells completed successfully")
    print("2. Verify you're using High-RAM runtime")
    print("3. Try restarting runtime and re-running setup")
```

---

## 8. Output Format

### CSV Structure

```csv
domain,connections,percentage
discovered-site.com,45,15.00
related-domain.org,38,12.67
another-site.net,32,10.67
example-news.com,28,9.33
```

### Pandas DataFrame Display

```
┌─────────────────────────┬─────────────┬────────────┐
│ Domain                  │ Connections │ Percentage │
├─────────────────────────┼─────────────┼────────────┤
│ discovered-site.com     │     45      │   15.00%   │
│ related-domain.org      │     38      │   12.67%   │
│ another-site.net        │     32      │   10.67%   │
│ example-news.com        │     28      │    9.33%   │
└─────────────────────────┴─────────────┴────────────┘
```

Sorted by connections (descending)

---

## 9. Limitations

### Technical Limitations

1. **Graph Snapshot:** Uses Nov-Dec 2024/Jan 2025 crawl data
2. **Domain-Level Only:** Host-level graph not included (100B+ edges)
3. **No Content Analysis:** Pure link topology, no text/semantic analysis
4. **Memory Bound:** Requires Colab Pro (50GB+ RAM)
5. **Processing Time:** 30 sec - 2 min per query (varies with seed list size)

### Methodological Limitations

1. **Link Spam:** May discover link farms or SEO schemes
2. **Legitimate Links:** Technical links (CDNs, ad networks) included
3. **Missing Data:** Domains not in CommonCrawl won't be found
4. **Temporal Lag:** 1-2 month delay between crawl and webgraph release

### Usage Limitations

1. **Session Timeout:** Colab Pro: 24 hours max
2. **Daily Quota:** No hard limit, but excessive use may trigger throttling
3. **Storage:** Google Drive needed for persistent caching

---

## 10. Future Enhancements

### Near-Term (Could Add to Notebook)

1. **Filtering Options:**
   - Exclude known CDNs/ad networks
   - Filter by TLD (.com, .org, etc.)
   - Domain blacklist/whitelist

2. **Visualization:**
   - Network graph of top results
   - Heatmap of connection strength
   - Venn diagram of overlapping connections

3. **Batch Processing:**
   - Upload CSV of multiple seed lists
   - Process all lists sequentially
   - Download combined results

4. **Quality Metrics:**
   - Domain age (from Whois)
   - PageRank score
   - Harmonic centrality

### Long-Term (Separate Tools)

1. **GNN Classifier:** Integrate reliability predictions
2. **Content Analysis:** Scrape and analyze article text
3. **Temporal Analysis:** Compare across multiple webgraph versions
4. **Multi-Hop Discovery:** Find domains 2-3 hops away

---

## Appendix A: Example Queries

### Example 1: Vaccine Misinformation
```
Seed Domains:
childrenshealthdefense.org
nvic.org
vaccinechoicecanada.com

Min Connections: 5
Direction: Backlinks

Expected Results: 200-500 related anti-vaccine websites
```

### Example 2: Political News Bias
```
Seed Domains:
breitbart.com
dailycaller.com
theblaze.com

Min Connections: 10
Direction: Outlinks

Expected Results: Commonly cited sources by these outlets
```

### Example 3: Link Scheme Detection
```
Seed Domains:
[Known link farm domains]

Min Connections: 3
Direction: Backlinks

Expected Results: Other domains in the link scheme
```

---

## Appendix B: Colab Pro Comparison

| Feature | Free | Pro ($10/month) | Pro+ ($50/month) |
|---------|------|-----------------|------------------|
| RAM | 12-15GB | 52GB | 83GB |
| Runtime | 12 hours | 24 hours | 24 hours |
| GPU | T4 | V100/A100 | V100/A100 |
| Background | No | Yes | Yes |
| **Suitable?** | ❌ No | ✅ Yes | ✅ Yes |

**Recommendation:** Pro is sufficient. Pro+ provides extra headroom but not necessary.

---

**END OF DESIGN SPECIFICATION**