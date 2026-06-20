"""Replace Space-Wizards-Federation -> Space-Wizards-Federation (simple string replace)."""

import os

BASE = r"D:\.sorcerers\docs"
EXTENSIONS = (".mdx", ".md", ".json")

def replace_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "Space-Wizards-Federation" not in content:
        return False
    
    content = content.replace("Space-Wizards-Federation", "Space-Wizards-Federation")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def main():
    changed = []
    for root, dirs, files in os.walk(BASE):
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            if f.endswith(EXTENSIONS):
                fp = os.path.join(root, f)
                if replace_in_file(fp):
                    changed.append(os.path.relpath(fp, BASE))
    
    print(f"Changed {len(changed)} files:")
    for c in sorted(changed):
        print(f"  {c}")

if __name__ == "__main__":
    main()
