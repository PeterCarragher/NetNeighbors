#!/usr/bin/env python3
"""
One-time script to find correct TLDs for casino domain names.

Searches the CommonCrawl webgraph for domains matching the casino names
and updates bad_casinos.csv with the full domain names.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Common TLDs to try, in order of preference
TLDS_TO_TRY = [
    ".com",
    ".net",
    ".org",
    ".casino",
    ".bet",
    ".io",
    ".co",
    ".eu",
    ".uk",
    ".de",
    ".info",
    ".biz",
    ".me",
    ".tv",
    ".cc",
    ".ag",  # Antigua - common for gambling
    ".gg",  # Common for gaming/gambling
]


def find_domain_tld(wg, name: str) -> Tuple[Optional[str], List[str]]:
    """
    Search for a domain name with various TLDs.

    Returns:
        Tuple of (preferred_domain, all_found_domains)
        preferred_domain is .com if found, otherwise first match
    """
    found = []

    for tld in TLDS_TO_TRY:
        full_domain = name + tld
        vid = wg.domain_to_id(full_domain)
        if vid is not None:
            found.append(full_domain)

    if not found:
        return None, []

    # Prefer .com if found
    for domain in found:
        if domain.endswith(".com"):
            return domain, found

    # Otherwise return first match
    return found[0], found


def main():
    # Add parent to path for example_loader import
    sys.path.insert(0, str(Path(__file__).parent))
    from example_loader import load_domains, get_example_data_path, setup_webgraph

    casino_file = get_example_data_path("bad_casinos.csv")

    # Load current names
    names = load_domains(str(casino_file))
    print(f"Loaded {len(names)} casino names")

    # Initialize webgraph
    webgraph_dir = os.environ.get("WEBGRAPH_DIR")
    webgraph_version = os.environ.get("WEBGRAPH_VERSION")

    setup_kwargs = {"auto_download": False}
    if webgraph_dir:
        setup_kwargs["webgraph_dir"] = webgraph_dir
    if webgraph_version:
        setup_kwargs["webgraph_version"] = webgraph_version

    wg = setup_webgraph(**setup_kwargs)

    # Search for each name
    results = []
    not_found = []
    multiple_found = []

    print("\nSearching for domains...")
    for i, name in enumerate(names):
        # Skip if already has a TLD (contains a dot)
        if "." in name:
            # Verify it exists
            vid = wg.domain_to_id(name)
            if vid is not None:
                results.append(name)
                print(f"  {name} - already valid")
            else:
                not_found.append(name)
                print(f"  {name} - NOT FOUND (has TLD but not in graph)")
            continue

        preferred, all_found = find_domain_tld(wg, name)

        if preferred:
            results.append(preferred)
            if len(all_found) > 1:
                multiple_found.append((name, all_found))
                print(f"  {name} -> {preferred} (also found: {', '.join(all_found)})")
            else:
                print(f"  {name} -> {preferred}")
        else:
            not_found.append(name)
            print(f"  {name} - NOT FOUND")

        if (i + 1) % 20 == 0:
            print(f"  ... processed {i + 1}/{len(names)}")

    # Summary
    print(f"\n=== Summary ===")
    print(f"Found: {len(results)}")
    print(f"Not found: {len(not_found)}")
    print(f"Multiple TLDs found: {len(multiple_found)}")

    if not_found:
        print(f"\nDomains not found in webgraph:")
        for name in not_found:
            print(f"  - {name}")

    if multiple_found:
        print(f"\nDomains with multiple TLDs (using .com preference):")
        for name, all_found in multiple_found:
            print(f"  - {name}: {', '.join(all_found)}")

    # Write updated file
    if results:
        print(f"\nWriting {len(results)} domains to {casino_file}")
        with open(casino_file, "w", encoding="utf-8") as f:
            for domain in sorted(results):
                f.write(domain + "\n")
        print("Done!")
    else:
        print("\nNo domains found - file not updated")


if __name__ == "__main__":
    main()
