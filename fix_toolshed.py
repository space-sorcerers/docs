"""Fix remaining toolshed files - replace all </div></div> with newlines."""

import os

BASE = r"D:\.sorcerers\docs"
FILES = [
    r"en\robust-toolbox\toolshed\commands\entity-control.mdx",
    r"en\robust-toolbox\toolshed\commands\general.mdx",
    r"en\robust-toolbox\toolshed\commands\misc.mdx",
]

for rel_path in FILES:
    full = os.path.join(BASE, rel_path)
    with open(full, "r", encoding="utf-8") as f:
        content = f.read()
    
    count = content.count("</div></div>")
    if count:
        content = content.replace("</div></div>", "</div>\n</div>")
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"FIXED {rel_path}: {count} occurrences")
    else:
        print(f"OK {rel_path}: no occurrences found")
