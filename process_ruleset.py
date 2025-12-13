import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent


def get_today_folder():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return BASE_DIR / "data" / today


def remove_marker_and_clean(folder: Path):
    """
    Remove any line containing either:
    -'this_ruleset_is_made_by_sukkaw.rules.skk.moe'
    - '7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe'
    from all .conf, .txt, .json files under folder.
    """
    markers = [
       "this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
        "This_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,This_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
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
            if any(m in line for m in markers):
                continue
            new_lines.append(line)

        if new_lines != lines:
            path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def process_apple_cdn(folder: Path):
    """
    1. Replace '.' with 'DOMAIN-SUFFIX,' before every URL entry
       in 'apple_cdn.conf' under domainset folder.
    2. Merge domainset/apple_cdn.conf and non_ip/apple_cdn.conf
       into one unified 'Apple_CDN.conf' in the same date folder.
    """
    domainset_conf = None
    non_ip_conf = None

    # Find both apple_cdn.conf files
    for path in folder.rglob("apple_cdn.conf"):
        parts = {p.lower() for p in path.parts}
        if "domainset" in parts:
            domainset_conf = path
        elif "non_ip" in parts:
            non_ip_conf = path

    # Rewrite domainset/apple_cdn.conf if present
    if domainset_conf and domainset_conf.is_file():
        lines = domainset_conf.read_text(encoding="utf-8", errors="ignore").splitlines()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue
            if "." in stripped:
                parts = stripped.split(".", 1)
                replaced = f"{parts[0]} DOMAIN-SUFFIX,{parts[1]}"
                new_lines.append(replaced)
            else:
                new_lines.append(line)
        domainset_conf.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Build unified Apple_CDN.conf
    unified_lines = []

    def append_file_lines(path: Path):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return
        unified_lines.extend(text.splitlines())

    if domainset_conf:
        append_file_lines(domainset_conf)
    if non_ip_conf:
        append_file_lines(non_ip_conf)

    if unified_lines:
        unified_path = folder / "Apple_CDN.conf"
        unified_path.write_text("\n".join(unified_lines) + "\n", encoding="utf-8")


def prefix_domain_suffix_in_domainset(folder: Path):
    """
    In any 'domainset' directory, for the files:
      - cdn.conf
      - download.conf
      - reject.conf
      - reject_extra.conf
      - reject_phishing.conf

    Prefix 'DOMAIN-SUFFIX,' to every non-empty, non-comment line.
    """
    target_filenames = {
        "cdn.conf",
        "download.conf",
        "reject.conf",
        "reject_extra.conf",
        "reject_phishing.conf",
    }

    for path in folder.rglob("*.conf"):
        if path.name not in target_filenames:
            continue

        # Only process files under a domainset directory
        parts_lower = {p.lower() for p in path.parts}
        if "domainset" not in parts_lower:
            continue

        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue

        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue
            # Avoid double prefix if already present
            if stripped.startswith("DOMAIN-SUFFIX,"):
                new_lines.append(line)
            else:
                new_lines.append(f"DOMAIN-SUFFIX,{stripped}")
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main():
    today_folder = get_today_folder()
    if not today_folder.exists():
        print(f"No folder found for today: {today_folder}")
        return

    remove_marker_and_clean(today_folder)
    process_apple_cdn(today_folder)
    prefix_domain_suffix_in_domainset(today_folder)


if __name__ == "__main__":
    main()
