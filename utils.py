"""
Utility functions for NetNeighbors discovery notebook.
"""

import os
import subprocess
import urllib.request

try:
    from tqdm.auto import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


def get_webgraph_files(version: str) -> list:
    """Return list of files required for a given webgraph version."""
    return [
        f"{version}-domain-vertices.txt.gz",
        f"{version}-domain.graph",
        f"{version}-domain.properties",
        f"{version}-domain-t.graph",
        f"{version}-domain-t.properties",
        f"{version}-domain.stats",
    ]


def check_ram(min_gb: int = 20) -> bool:
    """Check if sufficient RAM is available."""
    import psutil

    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"Available RAM: {ram_gb:.1f} GB")

    if ram_gb < min_gb:
        print(f"\nWARNING: You need at least {min_gb}GB RAM!")
        print(f"   Required: {min_gb}GB+ RAM")
        print(f"   You have: {ram_gb:.1f} GB")
        print("\n   Please enable High-RAM runtime:")
        print("   Runtime -> Change runtime type -> Runtime shape: High-RAM")
        return False
    else:
        print("Sufficient RAM available")
        return True


def _get_default_webgraph_dir() -> str:
    """Get default webgraph directory based on environment."""
    if os.path.exists("/content"):
        return "/content/webgraph"
    # Running from inside NetNeighbors, put webgraph in parent directory
    return os.path.join(os.path.dirname(os.getcwd()), "webgraph")


def mount_gcs_bucket(bucket_name: str, mount_path: str = None) -> str:
    """
    Mount a GCS bucket using gcsfuse.

    Args:
        bucket_name: GCS bucket name (without gs:// prefix)
        mount_path: Local path to mount the bucket. If None, uses default.

    Returns:
        The mount path if successful

    Raises:
        Exception if mounting fails
    """
    if mount_path is None:
        mount_path = _get_default_webgraph_dir()
    os.makedirs(mount_path, exist_ok=True)

    print(f"Mounting gs://{bucket_name} to {mount_path}...")
    try:
        subprocess.run(
            ['gcsfuse', '--implicit-dirs', bucket_name, mount_path],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"GCS bucket mounted successfully!")
        print(f"Webgraph directory: {mount_path}")
        return mount_path
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Failed to mount GCS bucket: {e.stderr}\n\n"
            "Make sure:\n"
            "  1. The bucket exists and you have access\n"
            "  2. You're authenticated (run: from google.colab import auth; auth.authenticate_user())"
        )


def setup_storage(bucket_name: str = None, webgraph_dir: str = None) -> str:
    """
    Setup storage for webgraph files.

    Args:
        bucket_name: GCS bucket name. If None, uses local storage.
        webgraph_dir: Directory for webgraph files. If None, auto-detects.

    Returns:
        Path to webgraph directory
    """
    if webgraph_dir is None:
        webgraph_dir = _get_default_webgraph_dir()

    if bucket_name:
        return mount_gcs_bucket(bucket_name, webgraph_dir)
    else:
        os.makedirs(webgraph_dir, exist_ok=True)
        print(f"Using local storage: {webgraph_dir}")
        if os.path.exists("/content"):
            print("Files will be downloaded each session (~15 min)")
        return webgraph_dir


def download_with_progress(url: str, dest_path: str) -> None:
    """Download file with progress bar if tqdm is available."""
    if os.path.exists(dest_path):
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"Already exists: {os.path.basename(dest_path)} ({size_mb:.1f} MB)")
        return

    print(f"Downloading: {os.path.basename(dest_path)}")

    if HAS_TQDM:
        def progress_hook(pbar):
            def update(_, block_size, total_size):
                if total_size > 0:
                    pbar.total = total_size
                    pbar.update(block_size)
            return update

        with tqdm(unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            urllib.request.urlretrieve(url, dest_path, reporthook=progress_hook(pbar))
    else:
        urllib.request.urlretrieve(url, dest_path)

    print(f"Downloaded: {os.path.basename(dest_path)}")


def _get_jar_path() -> str:
    """Find the cc-webgraph JAR file."""
    if os.path.exists("/content"):
        base = "/content"
    else:
        # Running from inside NetNeighbors, base is parent directory
        base = os.path.dirname(os.getcwd())

    jar_path = os.path.join(base, "cc-webgraph", "target",
                            "cc-webgraph-0.1-SNAPSHOT-jar-with-dependencies.jar")
    return jar_path


def build_offsets(webgraph_dir: str, version: str) -> None:
    """
    Build .offsets files required by WebGraph for random access.

    The offsets files are not provided by CommonCrawl and must be generated
    from the .graph files using the WebGraph library.

    Args:
        webgraph_dir: Directory containing the graph files
        version: Webgraph version string
    """
    jar_path = _get_jar_path()

    if not os.path.exists(jar_path):
        raise FileNotFoundError(
            f"cc-webgraph JAR not found at {jar_path}\n"
            "Please run setup.sh first to build cc-webgraph."
        )

    # Build offsets for both forward and transpose graphs
    graphs = [
        f"{version}-domain",      # Forward graph (outlinks)
        f"{version}-domain-t",    # Transpose graph (backlinks)
    ]

    for graph_name in graphs:
        graph_base = os.path.join(webgraph_dir, graph_name)
        offsets_file = f"{graph_base}.offsets"

        if os.path.exists(offsets_file):
            print(f"Offsets already exist: {graph_name}.offsets")
            continue

        print(f"Building offsets for {graph_name}...")

        cmd = [
            'java',
            '-cp', jar_path,
            'it.unimi.dsi.webgraph.BVGraph',
            '-O',  # Generate offsets only (capital O)
            '-L',  # Also generate Elias-Fano list (often needed)
            graph_base
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per graph
            )

            # Show output for debugging
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            if result.returncode != 0:
                raise Exception(f"Failed to build offsets for {graph_name}")

            # Verify the offsets file was created
            if os.path.exists(offsets_file):
                print(f"✅ Built {graph_name}.offsets")
            else:
                print(f"⚠️  Command succeeded but {graph_name}.offsets not found")
                print(f"   Expected at: {offsets_file}")

        except subprocess.TimeoutExpired:
            raise Exception(f"Timeout building offsets for {graph_name}")


def download_webgraph(webgraph_dir: str, version: str) -> None:
    """
    Download CommonCrawl webgraph files and build offsets.

    Args:
        webgraph_dir: Directory to download files to
        version: Webgraph version string (e.g., "cc-main-2025-26-nov-dec-jan")
    """
    base_url = f"https://data.commoncrawl.org/projects/hyperlinkgraph/{version}/domain"
    files = get_webgraph_files(version)

    print(f"Downloading CommonCrawl webgraph: {version}")
    print(f"Destination: {webgraph_dir}")
    print("=" * 60 + "\n")

    for filename in files:
        url = f"{base_url}/{filename}"
        dest = os.path.join(webgraph_dir, filename)
        download_with_progress(url, dest)

    print("\n" + "=" * 60)
    print("All graph files downloaded!")

    # Build offsets (required for random access)
    print("\nBuilding offset files (required for graph queries)...")
    build_offsets(webgraph_dir, version)

    print("\n" + "=" * 60)
    print("Webgraph ready for use!")
