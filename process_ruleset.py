import os
import datetime
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent


def get_today_folder():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return BASE_DIR / "data" / today


def remove_marker_lines(folder: Path):
    """
    1. Remove any line containing:
       - '7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe'
       - 'this_ruleset_is_made_by_sukkaw.ruleset.skk.moe'
       - 'DOMAIN,this_ruleset_is_made_by_sukkaw.ruleset.skk.moe'
       - 'DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe'
       from all .conf, .txt, .json files under folder.
    """
    markers = [
        "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
        "this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
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
            print(f"Cleaned markers from: {path.relative_to(BASE_DIR)}")


def normalize_domain_prefix(line: str) -> str:
    """
    If line already has DOMAIN, DOMAIN-SUFFIX, DOMAIN-SET, etc., return as-is.
    Otherwise, extract domain and prefix with DOMAIN-SUFFIX,.
    """
    stripped = line.strip()
    
    # Check if already has valid prefix
    if any(stripped.startswith(p) for p in ["DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-SET,", "DOMAIN-KEYWORD,", "#"]):
        return line
    
    if not stripped or stripped.startswith("#"):
        return line
    
    # Remove leading dot if present
    domain = stripped.lstrip(".")
    
    # Add prefix only if not empty
    if domain:
        return f"DOMAIN-SUFFIX,{domain}"
    
    return line


def process_domainset_and_non_ip(folder: Path):
    """
    2. Replace '.' or '-' at start of every URL entry (or normalize without prefix)
       with 'DOMAIN-SUFFIX,' prefix under "domainset" and "non_ip" folders (including subfolders).
       But skip if prefix already exists (check requirement 5).
    """
    # Process all .conf files in domainset and non_ip folders
    for path in folder.rglob("*.conf"):
        parts_lower = {p.lower() for p in path.parts}
        
        # Only process files under domainset or non_ip folders
        if "domainset" not in parts_lower and "non_ip" not in parts_lower:
            continue
        
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        
        new_lines = []
        changed = False
        
        for line in lines:
            normalized = normalize_domain_prefix(line)
            if normalized != line:
                changed = True
            new_lines.append(normalized)
        
        if changed:
            path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            print(f"Normalized domains in: {path.relative_to(BASE_DIR)}")


def extract_domains(path: Path) -> set:
    """
    Extract unique domain entries from a file.
    Handle lines with or without DOMAIN-SUFFIX, DOMAIN, etc.
    """
    domains = set()
    
    if not path.exists():
        return domains
    
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return domains
    
    for line in text.splitlines():
        stripped = line.strip()
        
        if not stripped or stripped.startswith("#"):
            continue
        
        # Remove known prefixes to get bare domain
        for prefix in ["DOMAIN-SUFFIX,", "DOMAIN,", "DOMAIN-SET,", "DOMAIN-KEYWORD,"]:
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix):].strip()
                break
        
        # Remove leading dots
        stripped = stripped.lstrip(".")
        
        if stripped:
            domains.add(stripped)
    
    return domains


def merge_and_deduplicate(folder: Path, source_name: str, target_name: str):
    """
    3/4. Merge two files (e.g., domainset/{source_name} and non_ip/{source_name})
         into one unified file (e.g., {target_name}).
         Remove source files after successful merge.
         Deduplicate by domain name (not by full line with prefix).
    """
    domainset_file = None
    non_ip_file = None
    
    # Find the source files
    for path in folder.rglob(source_name):
        parts_lower = {p.lower() for p in path.parts}
        if "domainset" in parts_lower:
            domainset_file = path
        elif "non_ip" in parts_lower:
            non_ip_file = path
    
    if not domainset_file and not non_ip_file:
        print(f"No source files found for {source_name}")
        return
    
    # Collect all unique domains
    all_domains = set()
    
    if domainset_file:
        all_domains |= extract_domains(domainset_file)
    
    if non_ip_file:
        all_domains |= extract_domains(non_ip_file)
    
    if not all_domains:
        print(f"No domains extracted for {source_name}")
        return
    
    # Write unified file with DOMAIN-SUFFIX prefix, sorted
    unified_lines = [f"DOMAIN-SUFFIX,{d}" for d in sorted(all_domains)]
    unified_path = folder / target_name
    
    unified_path.write_text("\n".join(unified_lines) + "\n", encoding="utf-8")
    print(f"Created unified: {unified_path.name} with {len(unified_lines)} entries")
    
    # Remove source files after successful creation
    if domainset_file and domainset_file.exists():
        try:
            domainset_file.unlink()
            print(f"Removed: {domainset_file.relative_to(BASE_DIR)}")
        except Exception as e:
            print(f"Failed to remove {domainset_file}: {e}")
    
    if non_ip_file and non_ip_file.exists():
        try:
            non_ip_file.unlink()
            print(f"Removed: {non_ip_file.relative_to(BASE_DIR)}")
        except Exception as e:
            print(f"Failed to remove {non_ip_file}: {e}")


def main():
    today_folder = get_today_folder()
    if not today_folder.exists():
        print(f"No folder found for today: {today_folder}")
        return

    print("=" * 60)
    print("Step 1: Remove marker lines...")
    print("=" * 60)
    remove_marker_lines(today_folder)
    
    print("\n" + "=" * 60)
    print("Step 2: Normalize domain prefixes in domainset & non_ip...")
    print("=" * 60)
    process_domainset_and_non_ip(today_folder)
    
    print("\n" + "=" * 60)
    print("Step 3: Merge apple_cdn.conf files...")
    print("=" * 60)
    merge_and_deduplicate(today_folder, "apple_cdn.conf", "Apple_CDN.conf")
    
    print("\n" + "=" * 60)
    print("Step 4: Merge cdn.conf files...")
    print("=" * 60)
    merge_and_deduplicate(today_folder, "cdn.conf", "CDN.conf")
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
