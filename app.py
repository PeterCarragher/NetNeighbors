"""
NetNeighbors Gradio App - Domain Discovery Using CommonCrawl Webgraph

A web interface for discovering related domains using link topology analysis.
Deployable to Google Cloud Run.
"""

import os
import gradio as gr
import pandas as pd
from typing import Tuple

# Import the graph bridge
from graph_bridge import GraphBridge

# Global bridge instance (loaded once at startup)
bridge = None


def get_bridge():
    """Get or initialize the graph bridge."""
    global bridge
    if bridge is None:
        # Get configuration from environment variables
        webgraph_dir = os.environ.get("WEBGRAPH_DIR", "/data/webgraph")
        version = os.environ.get("WEBGRAPH_VERSION", "cc-main-2024-feb-apr-may")
        jar_path = os.environ.get("CC_WEBGRAPH_JAR", None)

        print(f"Initializing GraphBridge...")
        print(f"  WEBGRAPH_DIR: {webgraph_dir}")
        print(f"  VERSION: {version}")

        bridge = GraphBridge(webgraph_dir, version, jar_path)
        bridge.load_graph()

    return bridge


def discover_domains(
    seeds_text: str,
    min_connections: int,
    direction: str
) -> Tuple[pd.DataFrame, str]:
    """
    Run domain discovery and return results.

    Args:
        seeds_text: Newline-separated list of seed domains
        min_connections: Minimum connections threshold
        direction: "backlinks" or "outlinks"

    Returns:
        Tuple of (results DataFrame, status message)
    """
    try:
        # Parse seed domains
        seeds = [s.strip().lower() for s in seeds_text.strip().split('\n') if s.strip()]

        if not seeds:
            return pd.DataFrame(), "Error: Please enter at least one domain"

        if len(seeds) > 10000:
            return pd.DataFrame(), f"Error: Maximum 10000 domains allowed (you entered {len(seeds)})"

        # Get bridge
        b = get_bridge()

        # Validate seeds
        found, not_found = b.validate_seeds(seeds)

        if not found:
            return pd.DataFrame(), f"Error: None of the {len(seeds)} domains were found in the webgraph"

        status_parts = [f"Found {len(found)}/{len(seeds)} seeds in graph"]

        if not_found and len(not_found) <= 5:
            status_parts.append(f"Not found: {', '.join(not_found)}")
        elif not_found:
            status_parts.append(f"Not found: {len(not_found)} domains")

        # Run discovery
        direction_val = "backlinks" if "backlinks" in direction.lower() else "outlinks"
        results = b.discover(found, min_connections, direction_val)

        if not results:
            status_parts.append("No domains found matching criteria")
            return pd.DataFrame(), " | ".join(status_parts)

        # Convert to DataFrame
        df = pd.DataFrame(results)
        status_parts.append(f"Found {len(df):,} domains with >= {min_connections} connections")

        return df, " | ".join(status_parts)

    except Exception as e:
        return pd.DataFrame(), f"Error: {str(e)}"


def create_app():
    """Create the Gradio application."""

    with gr.Blocks(
        title="NetNeighbors - Domain Discovery",
        theme=gr.themes.Soft()
    ) as app:

        gr.Markdown("""
        # 🔍 NetNeighbors: Domain Discovery

        Discover related domains using link topology analysis from the CommonCrawl web graph.

        **How it works:** Enter seed domains and find other domains connected via backlinks or outlinks.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                seeds_input = gr.Textbox(
                    label="Seed Domains",
                    placeholder="Enter domains, one per line:\ncnn.com\nbbc.com\nnytimes.com",
                    lines=10,
                    max_lines=20
                )

                min_conn = gr.Slider(
                    minimum=1,
                    maximum=100,
                    value=3,
                    step=1,
                    label="Minimum Connections",
                    info="Only show domains connected to at least this many seeds"
                )

                direction = gr.Radio(
                    choices=[
                        "Backlinks (who links TO seeds)",
                        "Outlinks (who seeds link TO)"
                    ],
                    value="Backlinks (who links TO seeds)",
                    label="Direction"
                )

                run_btn = gr.Button("🚀 Run Discovery", variant="primary")

            with gr.Column(scale=2):
                status_output = gr.Textbox(
                    label="Status",
                    interactive=False
                )

                results_output = gr.Dataframe(
                    label="Results",
                    headers=["domain", "connections", "percentage"],
                    interactive=False,
                    wrap=True
                )

        # Example inputs
        gr.Examples(
            examples=[
                ["cnn.com\nbbc.com\nnytimes.com\nwashingtonpost.com\nfoxnews.com", 3, "Backlinks (who links TO seeds)"],
                ["google.com\nfacebook.com\ntwitter.com", 2, "Outlinks (who seeds link TO)"],
            ],
            inputs=[seeds_input, min_conn, direction],
            label="Example Queries"
        )

        gr.Markdown("""
        ---
        **About:** Based on research by [Carragher et al. (ICWSM 2024)](https://arxiv.org/abs/2401.02379)
        on detection and discovery of misinformation sources using attributed webgraphs.

        **Data:** CommonCrawl webgraph with ~100M domains and 1.6B edges.
        """)

        # Connect the button
        run_btn.click(
            fn=discover_domains,
            inputs=[seeds_input, min_conn, direction],
            outputs=[results_output, status_output]
        )

    return app


# Create the app
app = create_app()

if __name__ == "__main__":
    # For local development
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False
    )
