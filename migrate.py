#!/usr/bin/env python3
"""Migrate The Robust Book from mdBook to Mintlify"""

import os
import re
import json
import shutil
from pathlib import Path

ROOT = Path(".")
SRC = ROOT / "src"
EN_SRC = SRC / "en"
RU_SRC = SRC / "ru"
EN_OUT = ROOT / "en"
RU_OUT = ROOT / "ru"
IMAGES_OUT = ROOT / "images"

TEMPLATE_INLINE = {
    "outdated.md": '<Danger title="Out of Date">\nThe information in this page is likely outdated and may no longer be relevant.\n</Danger>',
    "wip.md": '<Warning title="Work in Progress">\nThis page is a work in progress! Some information may be incomplete or outdated.\n</Warning>',
    "stub.md": '<Warning title="Stub">\nThis page is a stub and likely doesn\'t include enough useful information. You can help us by expanding it.\n</Warning>',
    "porting.md": '<Info title="Being Ported">\nThis page is in the process of being ported from the old documentation and is expected to look incorrect or be empty.\n</Info>',
    "legacy.md": '<Warning title="Attention: Legacy Documentation!">\nThis document is ported from before the game-area reorganization and needs to be updated\n</Warning>',
}

ADMONISH_MAP = {
    "note": "Note", "abstract": "Note", "info": "Info",
    "tip": "Tip", "success": "Success", "question": "Note",
    "warning": "Warning", "failure": "Warning", "danger": "Danger",
    "bug": "Warning", "example": "Note", "quote": "Note",
}


def flatten_list(lst):
    """Flatten nested lists one level."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def parse_summary():
    """Parse SUMMARY.md into a navigation tree."""
    text = SRC.joinpath("SUMMARY.md").read_text(encoding="utf-8")
    lines = text.split("\n")
    n = len(lines)

    # Identify section header lines: "Title\n====="
    section_starts = set()
    for i in range(n - 1):
        curr = lines[i].strip()
        nxt = lines[i + 1].strip()
        if curr and nxt and all(c == '=' for c in nxt) and len(nxt) > 3:
            section_starts.add(i)

    sections = []
    prev_header_idx = -1

    for idx in sorted(section_starts):
        header_name = lines[idx].strip()
        # Items are between this section's header and the next one
        start = idx + 2  # skip header and ==== line
        end = min((s for s in section_starts if s > idx), default=n)

        items = []
        for j in range(start, end):
            stripped = lines[j].strip()
            if not stripped:
                continue
            # Skip separator lines (--------)
            if all(c == '-' for c in stripped) and len(stripped) > 3:
                continue
            # Skip ===== lines (shouldn't happen, but just in case)
            if all(c == '=' for c in stripped) and len(stripped) > 3:
                continue
            # Skip the index link "[The Robust Book](index.md)" at top
            if stripped.startswith("- [") and "[The Robust Book]" in stripped:
                continue
            if stripped.startswith("- [") or stripped.startswith("- ["):
                items.append(lines[j].rstrip())

        sections.append((header_name, items))
        prev_header_idx = idx

    return sections


def parse_items_to_nav_group(items_text):
    """Parse a list of markdown link items into navigation structure."""
    page_pattern = re.compile(r'^(\s*)- \[([^\]]+)\]\(([^)]*)\)\s*$')

    # Parse items to (indent, name, slug) tuples
    parsed = []
    for item_text in items_text:
        m = page_pattern.match(item_text)
        if not m:
            continue
        indent = len(m.group(1))
        name = m.group(2).strip()
        path = m.group(3).strip()
        if not path:
            continue
        slug = path.replace(".md", "")
        parsed.append((indent, name, slug))

    def build(items):
        """Build tree from flat list with indent levels."""
        if not items:
            return []

        base_indent = items[0][0]
        result = []
        i = 0
        while i < len(items):
            indent, name, slug = items[i]

            if indent != base_indent:
                break

            # Look ahead: does the next item have deeper indent?
            if i + 1 < len(items) and items[i + 1][0] > indent:
                # Collect children (all items with indent > current)
                children = []
                i += 1
                while i < len(items) and items[i][0] > indent:
                    children.append(items[i])
                    i += 1
                sub = build(children)
                if slug:
                    result.append({
                        "group": name,
                        "root": slug,
                        "pages": sub
                    })
                else:
                    result.append({
                        "group": name,
                        "pages": sub
                    })
            else:
                # Plain page (or empty-link without path)
                result.append(slug)
                i += 1

        return result

    return build(parsed)


def nav_tree_to_json(tree):
    """Convert navigation tree to docs.json format (simple pass-through)."""
    return tree


def generate_docs_json():
    """Generate the docs.json configuration file."""
    sections = parse_summary()

    en_groups = []
    for section_name, items in sections:
        nav_tree = parse_items_to_nav_group(items)
        json_items = nav_tree_to_json(nav_tree)
        if json_items:
            en_groups.append({
                "group": section_name,
                "pages": json_items
            })

    docs_config = {
        "$schema": "https://mintlify.com/docs.json",
        "theme": "linden",
        "name": "Space Wizards Development Wiki",
        "colors": {
            "primary": "#b195d5"
        },
        "favicon": "/favicon.png",
        "navigation": {
            "languages": [
                {
                    "language": "en",
                    "groups": en_groups
                },
                {
                    "language": "ru",
                    "groups": [
                        {
                            "group": "Введение",
                            "pages": ["ru/index"]
                        }
                    ]
                }
            ]
        },
        "metadata": {
            "timestamp": True
        },
        "footer": {
            "socials": {
                "github": "https://github.com/space-wizards-federation/docs",
                "discord": "https://discord.gg/ss14"
            }
        }
    }

    return docs_config


def copy_images():
    """Copy all image assets from src/en/assets/ to images/."""
    assets_dir = EN_SRC / "assets"
    if assets_dir.exists():
        if IMAGES_OUT.exists():
            shutil.rmtree(IMAGES_OUT)
        # Copy each subdirectory individually, flattening the "images/" subdir
        for subdir in assets_dir.iterdir():
            if subdir.is_dir():
                if subdir.name == "images":
                    # Flatten: src/en/assets/images/* -> images/*
                    for item in subdir.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, IMAGES_OUT / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, IMAGES_OUT / item.name)
                    print(f"  Flattened {subdir} -> {IMAGES_OUT}")
                else:
                    shutil.copytree(subdir, IMAGES_OUT / subdir.name, dirs_exist_ok=True)
                    print(f"  Copied {subdir} -> {IMAGES_OUT / subdir.name}")
        print(f"  Copied images to {IMAGES_OUT}")

    # Copy theme favicon
    favicon = ROOT / "theme" / "favicon.png"
    if favicon.exists():
        shutil.copy2(favicon, ROOT / "favicon.png")
        print(f"  Copied favicon to root")

    # Also handle images in other locations (media/ dirs etc.)
    other_images = list(ROOT.glob("src/en/space-station-14/**/media/*"))
    other_images.extend(ROOT.glob("src/en/ss14-by-example/**/media/*"))
    for img in other_images:
        if img.is_file() and img.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
            rel = img.relative_to(SRC / "en")
            dst = IMAGES_OUT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img, dst)
            print(f"  Copied {img} to {dst}")


def convert_admonish(content):
    """Convert ```admonish blocks to Mintlify components."""
    pattern = r'```admonish\s+(\w+)(?:\s+"([^"]*)")?\s*\n(.*?)```'
    def repl(m):
        type_ = m.group(1).lower()
        title = m.group(2) or ""
        body = m.group(3).strip()
        mint_type = ADMONISH_MAP.get(type_, "Note")
        if title:
            return f'<{mint_type} title="{title}">\n{body}\n</{mint_type}>'
        else:
            return f'<{mint_type}>\n{body}\n</{mint_type}>'
    return re.sub(pattern, repl, content, flags=re.DOTALL)


def convert_templates(content):
    """Convert {{#template ...}} calls to inline content."""
    pattern = r'\{\{#template\s+([^}]+)\}\}'
    def repl(m):
        template_ref = m.group(1).strip()
        parts = template_ref.split('\n')
        main_path = parts[0].strip()
        tmpl_name = main_path.rsplit('/', 1)[-1] if '/' in main_path else main_path

        if tmpl_name in TEMPLATE_INLINE:
            return TEMPLATE_INLINE[tmpl_name]
        elif 'toolshed-command-head.md' in tmpl_name:
            name_val = ""
            typesig_val = ""
            for line in parts[1:]:
                line = line.strip()
                if line.startswith('name='):
                    name_val = line[5:].strip()
                elif line.startswith('typesig='):
                    typesig_val = line[8:].strip()
            if name_val:
                return (f'<div style="display: flex; justify-content: space-between; '
                        f'align-items: center;">\n<div>\n<h3>{name_val}</h3>\n</div>\n'
                        f'<div style="text-align: right;">\n\n`{typesig_val}`</div></div>')
            return ''
        else:
            return ''
    return re.sub(pattern, repl, content, flags=re.DOTALL)


def convert_details(content):
    """Convert <details><summary> to <Accordion>."""
    pattern = r'<details>\s*\n?\s*<summary>(.*?)</summary>\s*\n?(.*?)</details>'
    def repl(m):
        title = m.group(1).strip()
        body = m.group(2).strip()
        return f'<Accordion title="{title}">\n{body}\n</Accordion>'
    return re.sub(pattern, repl, content, flags=re.DOTALL)


def fix_image_paths(content, src_rel_depth):
    """Fix relative image paths to absolute /images/ paths."""
    # Handle various relative depths to assets/
    # src_rel_depth = number of directory components from root to the file
    # e.g., for "en/meta/X.md": depth = 2, "../" from file → "en/"
    # We need to replace N levels of "../assets/" with "/images/"

    # Simple approach: replace all known patterns
    # From depth 1 (en/*.md): ../assets/ → /images/
    # From depth 2 (en/section/*.md): ../../assets/ → /images/
    # From depth 3 (en/section/sub/*.md): ../../../assets/ → /images/
    # etc.

    # Replace any number of ../ followed by assets/ with /images/
    # images subdirectory is flattened into /images/ directly
    content = re.sub(r'(?:\.\./)+assets/images/', '/images/', content)
    content = re.sub(r'(?:\.\./)+assets/misc/', '/images/misc/', content)
    content = re.sub(r'(?:\.\./)+assets/engine-development/', '/images/engine-development/', content)

    # Handle <img> tags with en/assets/ paths
    content = re.sub(r'<img\s+([^>]*)src="en/assets/', '<img \\1src="/images/', content)

    # Handle references that start with assets/ (for root files like index.md, 404.md)
    content = re.sub(r'\(assets/images/', '(/images/', content)
    content = re.sub(r'src="assets/images/', 'src="/images/', content)

    return content


def convert_file(src_path, dst_path):
    """Convert a single .md file to .mdx."""
    raw = src_path.read_bytes()
    # Handle both \r\n and \n
    if b'\r\n' in raw:
        content = raw.decode('utf-8').replace('\r\n', '\n')
    else:
        content = raw.decode('utf-8')

    # 1. Extract title from first H1
    title = None
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('# ') and not line.startswith('## ') and title is None:
            title = line[2:].strip()
            continue
        new_lines.append(line)
    content = '\n'.join(new_lines)

    # 2. Remove {{#title ...}} and {{#include ...}} and {{#embed ...}} directives
    content = re.sub(r'\{\{#title\s+[^}]*\}\}\s*\n?', '', content)
    content = re.sub(r'\{\{#include\s+[^}]*\}\}\s*\n?', '', content)
    content = re.sub(r'\{\{#embed\s+[^}]*\}\}\s*\n?', '', content)

    # 3. Convert admonish blocks
    content = convert_admonish(content)

    # 4. Convert templates
    content = convert_templates(content)

    # 5. Convert <details> to <Accordion>
    content = convert_details(content)

    # 6. Fix internal .md links (but for images use separate handling)
    content = re.sub(r'\(([^()]+)\.md(#[\w-]+)?\)',
                     lambda m: f'({m.group(1)}{m.group(2) or ""})', content)

    # 7. Fix LaTeX delimiters
    content = content.replace('\\[', '$$').replace('\\]', '$$')
    content = content.replace('\\(', '$').replace('\\)', '$')

    # 8. Fix code block languages (remove = suffix)
    content = re.sub(r'```(\w+)=', r'```\1', content)

    # 9. Fix image paths
    # Calculate relative depth from root to determine asset path prefix
    rel_parts = src_path.relative_to(SRC).parts
    content = fix_image_paths(content, len(rel_parts))

    # 10. Add frontmatter
    if title:
        fm_title = title.replace('"', "'")
        frontmatter = f'---\ntitle: "{fm_title}"\n---\n\n'
        content = frontmatter + content

    # Write
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(content, encoding='utf-8')
    print(f"  Converted: {src_path} -> {dst_path}")


def process_en_files():
    """Process all English .md files."""
    md_files = list(EN_SRC.rglob("*.md"))
    for src_path in md_files:
        rel = src_path.relative_to(SRC)
        # Remove .md extension, add .mdx
        dst_rel = rel.with_suffix(".mdx")
        dst_path = ROOT / dst_rel
        convert_file(src_path, dst_path)


def process_ru_files():
    """Process Russian .md files - just copy as is for now."""
    md_files = list(RU_SRC.rglob("*.md"))
    for src_path in md_files:
        rel = src_path.relative_to(SRC)
        dst_rel = rel.with_suffix(".mdx")
        dst_path = ROOT / dst_rel
        # Russian files are mostly empty templates, just copy converting basic things
        content = src_path.read_text(encoding='utf-8')
        # Add basic frontmatter
        title = "Russian Page"
        # Try to extract title
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line[2:].strip()
                break
        content = convert_admonish(content)
        frontmatter = f'---\ntitle: "{title}"\n---\n\n'
        content = frontmatter + content
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text(content, encoding='utf-8')
        print(f"  Converted (ru): {src_path} -> {dst_path}")


def process_root_files():
    """Process root-level files (index.md, 404.md)."""
    for fname in ["index.md", "404.md"]:
        src = SRC / fname
        if src.exists():
            dst = ROOT / fname.replace(".md", ".mdx")
            convert_file(src, dst)


def create_ru_index():
    """Create Russian language index page."""
    ru_index = RU_OUT / "index.mdx"
    ru_index.parent.mkdir(parents=True, exist_ok=True)
    content = """---
title: "Документация Space Wizards"
---

<img src="/images/misc/icon-trans.svg" width=128 style="margin-left:auto;margin-right:auto;display:block"/>

<Warning title="В разработке">
Русская версия документации находится в разработке.
</Warning>

Добро пожаловать в вики разработчиков Space Wizards Federation!

Этот сайт содержит техническую документацию для движка Robust Toolbox и игры Space Station 14.

## Начало работы

- [:question: Как я могу начать программировать?](/en/general-development/setup/howdoicode)
"""
    ru_index.write_text(content, encoding='utf-8')
    print(f"  Created: {ru_index}")


def main():
    print("=" * 60)
    print("Migrating The Robust Book from mdBook to Mintlify")
    print("=" * 60)

    # 1. Copy images
    print("\n[1/7] Copying images...")
    copy_images()

    # 2. Create output directories
    EN_OUT.mkdir(parents=True, exist_ok=True)
    RU_OUT.mkdir(parents=True, exist_ok=True)

    # 3. Process root files
    print("\n[2/7] Processing root files...")
    process_root_files()

    # 4. Process English files
    print("\n[3/7] Processing English files...")
    process_en_files()

    # 5. Process Russian files
    print("\n[4/7] Processing Russian files...")
    process_ru_files()

    # 6. Create Russian index
    print("\n[5/7] Creating Russian index...")
    create_ru_index()

    # 7. Generate docs.json
    print("\n[6/7] Generating docs.json...")
    docs_config = generate_docs_json()
    docs_json_path = ROOT / "docs.json"
    docs_json_path.write_text(json.dumps(docs_config, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"  Created: {docs_json_path}")

    print("\n[7/7] Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
