#!/usr/bin/env python3

# This script checks if all documents in the repository are linked in docs.json
# navigation so that they can be reached via the website.

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()

DOCS_DIRS = [
    REPO_ROOT / r"en",
]

EXEMPT_DIRS = [
    REPO_ROOT / r"images",
    REPO_ROOT / r"en/templates",
]

NAV_FILE = REPO_ROOT / r"docs.json"


def get_nav_links():
    """Parse docs.json and return set of linked page paths (absolute)."""
    links = set()
    data = json.loads(NAV_FILE.read_text(encoding="utf-8"))

    def walk_pages(pages):
        for item in pages:
            if isinstance(item, str):
                # "en/community/hub-rules"
                abs_path = (NAV_FILE.parent / item).resolve()
                # Try with .mdx extension
                with_mdx = abs_path.with_suffix(".mdx")
                if with_mdx.exists():
                    links.add(with_mdx)
                elif abs_path.exists():
                    links.add(abs_path)
            elif isinstance(item, dict):
                # {"group": "...", "pages": [...]} or {"group": "...", "root": "...", "pages": [...]}
                if "root" in item:
                    root_path = (NAV_FILE.parent / item["root"]).resolve()
                    with_mdx = root_path.with_suffix(".mdx")
                    if with_mdx.exists():
                        links.add(with_mdx)
                    elif root_path.exists():
                        links.add(root_path)
                if "pages" in item:
                    walk_pages(item["pages"])

    for lang in data.get("navigation", {}).get("languages", []):
        walk_pages(lang.get("groups", []))

    return links


def get_all_docs(folder: Path):
    """Collect all .mdx files in the given folder, skipping exempt folders."""
    exempt_resolved = [ex.resolve() for ex in EXEMPT_DIRS]

    docs = set()
    for p in folder.rglob("*.mdx"):
        if any(ex in p.resolve().parents for ex in exempt_resolved):
            continue
        docs.add(p.resolve())

    return docs


def main() -> int:
    nav_links = get_nav_links()
    print(f"found {len(nav_links)} linked pages in docs.json")
    missing_any = False

    for docs_dir in DOCS_DIRS:
        docs = get_all_docs(docs_dir)
        print(f"found {len(docs)} .mdx files in {docs_dir}")
        missing = [d for d in docs if d not in nav_links]

        if missing:
            print(f"❌ The following docs in {docs_dir} are not linked in docs.json:")
            for m in missing:
                print(" -", m.relative_to(Path.cwd()))
            missing_any = True
        else:
            print(f"✅ All docs in {docs_dir} are linked in docs.json")

    return 1 if missing_any else 0


exit(main())
