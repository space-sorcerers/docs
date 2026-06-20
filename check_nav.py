import json

with open("docs.json") as f:
    cfg = json.load(f)

nav = cfg["navigation"]["languages"][0]["groups"]
print(f"Section count: {len(nav)}")
for g in nav:
    print(f"  Section: {g['group']} ({len(g['pages'])} items)")
    for p in g["pages"][:4]:
        if isinstance(p, str):
            print(f"    Page: {p}")
        elif isinstance(p, dict):
            children = p.get("pages", [])
            root = p.get("root", "none")
            print(f"    Group: {p['group']} ({len(children)} children, root={root})")
            for c in children[:2]:
                if isinstance(c, str):
                    print(f"      Page: {c}")
                elif isinstance(c, dict):
                    print(f"      SubGroup: {c['group']} ({len(c.get('pages', []))} children)")
    if len(g["pages"]) > 4:
        print(f"    ... ({len(g['pages']) - 4} more)")
