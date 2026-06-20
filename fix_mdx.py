"""Fix common MDX parsing errors in converted files."""

import re
import os

BASE = r"D:\.sorcerers\docs"

# Files with specific fixes: (file_path, [(old, new), ...])
SPECIFIC_FIXES = {
    r"en\general-development\game-area-design-doc.mdx": [
        ("<br>", "<br />"),
    ],
    r"en\general-development\setup\git-for-the-ss14-developer.mdx": [
        ("<hr>", "<hr />"),
    ],
    r"en\community\space-wizards-hub-rules.mdx": [
        ("<!--", "{/*"),
        ("-->", "*/}"),
    ],
    r"en\robust-toolbox\rendering\shaders.mdx": [
        ("<!--", "{/*"),
        ("-->", "*/}"),
    ],
    r"en\robust-toolbox\transform\grids.mdx": [
        ('<!--Lol image nerd-->', ''),
    ],
    r"en\server-hosting\setting-up-ss14-watchdog.mdx": [
        ("<!--", "{/*"),
        ("-->", "*/}"),
    ],
    r"en\space-station-14\core-tech\device-network.mdx": [
        ("<!--The wired network component connects to the wired device network, which currently uses power cables for connecting devices to each other.\nThis means that every wired network connection that is connected to the same power source is on the same wired network.\n-->", "{/*The wired network component connects to the wired device network, which currently uses power cables for connecting devices to each other.\nThis means that every wired network connection that is connected to the same power source is on the same wired network.\n*/}"),
    ],
    r"en\general-development\codebase-info\conventions.mdx": [
        ("ProtoId<T>", "ProtoId`<T>`"),
    ],
    r"en\general-development\tips\prs-with-engine-changes.mdx": [
        ('"Requires <PR>"', '"Requires `<PR>`"'),
    ],
    r"en\space-station-14\departments\service\proposals\theshued-librarian-gameplay.mdx": [
        ("List<Enum>", "`List<Enum>`"),
    ],
    r"en\ss14-by-example\ui-and-you.mdx": [
        ("this.CreateWindow<TWindow>()", "`this.CreateWindow<TWindow>()`"),
    ],
    r"en\general-development\tips\beginner-faq.mdx": [
        ("<==>", "`<==>`"),
    ],
    r"en\space-station-14\core-tech\npcs.mdx": [
        ("Dictionary<string, object>", "`Dictionary<string, object>`"),
    ],
    r"en\community\admin\wizards-den-mrp-policy.mdx": [
        ("Round <#>. <offense> Strike. <description>", "`Round <#>. <offense> Strike. <description>`"),
    ],
    r"en\space-station-14\mapping\guides\general-guide.mdx": [
        ("<0-9>", "`<0-9>`"),
    ],
    r"en\space-station-14\round-flow\proposals\revolutionaries-codeword-rework.mdx": [
        ("<**50%**", "`<50%`"),
    ],
    r"en\space-station-14\departments\science\anomaly-cores.mdx": [
        ('width=64 height=64 style="image-rendering: pixelated"', 'width="64" height="64" style={{imageRendering: "pixelated"}}'),
    ],
    r"en\space-station-14\round-flow\proposals\rogue-drones.mdx": [
        ('width=64 height=64 style="image-rendering: pixelated"', 'width="64" height="64" style={{imageRendering: "pixelated"}}'),
    ],
    r"index.mdx": [
        ('width=128 style="margin-left:auto;margin-right:auto;display:block"', 'width={128} style={{marginLeft: "auto", marginRight: "auto", display: "block"}}'),
    ],
    r"ru\index.mdx": [
        ('width=128 style="margin-left:auto;margin-right:auto;display:block"', 'width={128} style={{marginLeft: "auto", marginRight: "auto", display: "block"}}'),
    ],
}

# Files with acorn errors - embed youtube
YOUTUBE_EMBEDS = {
    r"en\general-development\setup\server-hosting-tutorial.mdx": (
        '{% embed youtube id="IDBqrAGZ3cA" loading="lazy" %}',
        '<iframe src="https://www.youtube.com/embed/IDBqrAGZ3cA" loading="lazy" style="width:100%;aspect-ratio:16/9;border:none;border-radius:8px"></iframe>'
    ),
    r"en\general-development\setup\setting-up-a-development-environment.mdx": (
        '{% embed youtube id="EUGl_zNS6Uk?t=3" loading="lazy" %}',
        '<iframe src="https://www.youtube.com/embed/EUGl_zNS6Uk?t=3" loading="lazy" style="width:100%;aspect-ratio:16/9;border:none;border-radius:8px"></iframe>'
    ),
}

# Files with {{ #template }} acorn errors
TEMPLATE_INCLUDES = {
    r"en\robust-toolbox\user-interface.mdx": (
        '{{ #template ../templates/outdated.md }}',
        '<Danger title="Out of Date">The information in this page is likely outdated and may no longer be relevant.</Danger>'
    ),
    r"en\ss14-by-example\introduction-to-ss14-by-example.mdx": (
        '{{ #template ../templates/outdated.md }}',
        '<Danger title="Out of Date">The information in this page is likely outdated and may no longer be relevant.</Danger>'
    ),
    r"en\ss14-by-example\ui-survival-guide.mdx": (
        '{{ #template ../templates/outdated.md }}',
        '<Danger title="Out of Date">The information in this page is likely outdated and may no longer be relevant.</Danger>'
    ),
}

# Toolshed files with </div></div> issues
TOOLSHED_FIXES = {
    r"en\robust-toolbox\toolshed\commands\entity-control.mdx": (
        "`[none] -> IEnumerable<EntityUid>`</div></div>",
        "`[none] -> IEnumerable<EntityUid>`\n</div>\n</div>"
    ),
    r"en\robust-toolbox\toolshed\commands\general.mdx": (
        "`[[#typesig]]`</div></div>",
        "`[[#typesig]]`\n</div>\n</div>"
    ),
    r"en\robust-toolbox\toolshed\commands\misc.mdx": (
        "`[[#typesig]]`</div></div>",
        "`[[#typesig]]`\n</div>\n</div>"
    ),
    r"en\templates\toolshed-command-head.mdx": (
        "`[[#typesig]]`</div></div>",
        "`[[#typesig]]`\n</div>\n</div>"
    ),
    r"ru\templates\toolshed-command-head.mdx": (
        "`[[#typesig]]`</div></div>",
        "`[[#typesig]]`\n</div>\n</div>"
    ),
}

# Fix </Info> adjacent text
ADJACENT_TAG_FIXES = {
    r"en\ss14-by-example\adding-a-simple-bikehorn.mdx": (
        "</Info>EmitSoundOnUse```",
        "</Info>\n\n`EmitSoundOnUse`"
    ),
}


def fix_file(filepath, replacements):
    full_path = os.path.join(BASE, filepath)
    if not os.path.exists(full_path):
        print(f"  SKIP (not found): {filepath}")
        return False
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"  FIXED: {filepath}")
        else:
            print(f"  SKIP (not matched): {filepath} -- {old[:40]}")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def main():
    print("=== Applying specific fixes ===")
    for filepath, replacements in SPECIFIC_FIXES.items():
        fix_file(filepath, replacements)

    print("\n=== Fixing YouTube embeds ===")
    for filepath, (old, new) in YOUTUBE_EMBEDS.items():
        fix_file(filepath, [(old, new)])

    print("\n=== Fixing template includes ===")
    for filepath, (old, new) in TEMPLATE_INCLUDES.items():
        fix_file(filepath, [(old, new)])

    print("\n=== Fixing toolshed divs ===")
    for filepath, (old, new) in TOOLSHED_FIXES.items():
        fix_file(filepath, [(old, new)])

    print("\n=== Fixing adjacent tags ===")
    for filepath, (old, new) in ADJACENT_TAG_FIXES.items():
        fix_file(filepath, [(old, new)])

    print("\nDone!")


if __name__ == "__main__":
    main()
