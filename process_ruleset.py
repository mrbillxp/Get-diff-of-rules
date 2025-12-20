import datetime
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent


def get_today_folder():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return BASE_DIR / "data" / today


def remove_marker_lines(folder: Path):
    """
    Remove any line containing (case insensitive):
      - '7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe'
      - 'this_ruleset_is_made_by_sukkaw.ruleset.skk.moe'
      - 'DOMAIN,this_ruleset_is_made_by_sukkaw.ruleset.skk.moe'
      - 'DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe'
    """
    markers = [
        "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
        "this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "this_ruleset_is_made_by_sukkaw",
        "7h1s_rul35et_i5_mad3_by_5ukk4w",
    ]

    targets = list(folder.rglob("*.conf")) + list(folder.rglob("*.txt")) + list(folder.rglob("*.json"))

    for path in targets:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = text.splitlines()
        new_lines = []
        for line in lines:
            if any(m.lower() in line.lower() for m in markers):
                continue
            new_lines.append(line)

        if new_lines != lines:
            path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def process_dot_entries(folder: Path):
    """
    Replace entries starting with '.' to 'DOMAIN-SUFFIX,.'
    BUT ONLY if they don't already have a prefix like:
      - DOMAIN-KEYWORD
      - DOMAIN
      - URL-REGEX
      - DOMAIN-SET
      - DOMAIN-WILDCARD
      - DOMAIN-SUFFIX
    """
    protected_prefixes = {
        "DOMAIN-KEYWORD",
        "DOMAIN-WILDCARD",
        "DOMAIN-SET",
        "URL-REGEX",
        "DOMAIN-SUFFIX",
        "DOMAIN",  # Must check this last since it's a substring of others
    }

    targets = list(folder.rglob("*.conf")) + list(folder.rglob("*.txt"))

    for path in targets:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = text.splitlines()
        new_lines = []
        modified = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue

            # Check if line already has any protected prefix
            has_protected_prefix = False
            for prefix in protected_prefixes:
                if stripped.startswith(prefix):
                    has_protected_prefix = True
                    break

            # If no protected prefix and starts with '.', add DOMAIN-SUFFIX,
            if not has_protected_prefix and stripped.startswith("."):
                new_line = f"DOMAIN-SUFFIX,{stripped}"
                new_lines.append(new_line)
                modified = True
            else:
                new_lines.append(line)

        if modified:
            path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def merge_and_remove_files(folder: Path, filename_pattern: str, output_filename: str):
    """
    Merge files matching a pattern from domainset/ and non_ip/ folders.
    Example: filename_pattern="apple_cdn.conf", output_filename="Apple_CDN.conf"
    """
    domainset_path = None
    non_ip_path = None

    # Find both files
    for path in folder.rglob(filename_pattern):
        parts_lower = {p.lower() for p in path.parts}
        if "domainset" in parts_lower:
            domainset_path = path
        elif "non_ip" in parts_lower:
            non_ip_path = path

    # Merge content
    merged_lines = []

    def append_file_content(file_path: Path):
        if file_path and file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                merged_lines.extend(content.splitlines())
            except Exception:
                pass

    append_file_content(domainset_path)
    append_file_content(non_ip_path)

    # Write merged file
    if merged_lines:
        output_path = folder / output_filename
        output_path.write_text("\n".join(merged_lines) + "\n", encoding="utf-8")

        # Remove original files
        if domainset_path and domainset_path.is_file():
            domainset_path.unlink()
        if non_ip_path and non_ip_path.is_file():
            non_ip_path.unlink()


def main():
    today_folder = get_today_folder()
    if not today_folder.exists():
        print(f"No folder found for today: {today_folder}")
        return

    print("Step 1: Removing marker lines...")
    remove_marker_lines(today_folder)

    print("Step 2: Processing dot entries (adding DOMAIN-SUFFIX, prefix)...")
    process_dot_entries(today_folder)

    print("Step 3: Merging apple_cdn.conf files...")
    merge_and_remove_files(today_folder, "apple_cdn.conf", "Apple_CDN.conf")

    print("Step 4: Merging cdn.conf files...")
    merge_and_remove_files(today_folder, "cdn.conf", "CDN.conf")

    print("Done!")


if __name__ == "__main__":
    main()
