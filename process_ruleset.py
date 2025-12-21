import datetime
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent


def get_today_folder():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return BASE_DIR / "data" / today


def should_remove_line(line: str) -> bool:
    """
    Check if line contains any of the marker strings that should be removed.
    """
    markers = [
        "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
        "this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
    ]
    return any(marker in line for marker in markers)


def has_reserved_prefix(line: str) -> bool:
    """
    Check if line already has a reserved prefix that should NOT be replaced.
    Reserved prefixes: DOMAIN-KEYWORD, DOMAIN, URL-REGEX, DOMAIN-SET, DOMAIN-WILDCARD
    """
    stripped = line.strip()
    reserved_prefixes = [
        "DOMAIN-KEYWORD,",
        "URL-REGEX,",
        "DOMAIN-SET,",
        "DOMAIN-WILDCARD,",
        "DOMAIN,",  # Check DOMAIN, last to avoid matching substrings
    ]
    return any(stripped.startswith(p) for p in reserved_prefixes)


def process_line_for_domain_suffix(line: str) -> str:
    """
    If line starts with a dot (.) and has no reserved prefix, 
    replace dot with 'DOMAIN-SUFFIX,' prefix.
    Otherwise, return unchanged.
    """
    stripped = line.strip()
    
    # Skip empty lines and comments
    if not stripped or stripped.startswith("#"):
        return line
    
    # If has reserved prefix, don't modify
    if has_reserved_prefix(stripped):
        return line
    
    # If starts with dot, replace with DOMAIN-SUFFIX,
    if stripped.startswith("."):
        # Remove leading dot and add DOMAIN-SUFFIX,
        domain_part = stripped.lstrip(".")
        return f"DOMAIN-SUFFIX,{domain_part}"
    
    return line


def clean_and_process_files(folder_path: Path):
    """
    Process all .conf files in folder:
    1. Remove lines with markers
    2. Replace leading dots with DOMAIN-SUFFIX, (preserving reserved prefixes)
    """
    if not folder_path.exists():
        print(f"Folder not found: {folder_path}")
        return
    
    conf_files = list(folder_path.rglob("*.conf"))
    print(f"Processing {len(conf_files)} files in {folder_path.name}/")
    
    for conf_path in conf_files:
        try:
            text = conf_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  ⚠️ Failed to read {conf_path.name}: {e}")
            continue
        
        lines = text.splitlines()
        new_lines = []
        
        for line in lines:
            # Step 1: Remove marker lines
            if should_remove_line(line):
                continue
            
            # Step 2: Process line for DOMAIN-SUFFIX, replacement
            processed_line = process_line_for_domain_suffix(line)
            new_lines.append(processed_line)
        
        # Write back if changed
        if new_lines != lines:
            conf_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            print(f"  ✓ {conf_path.name}: cleaned")


def merge_and_deduplicate_files(
    folder_path: Path, 
    source_filename: str, 
    output_filename: str,
    remove_source: bool = True
) -> bool:
    """
    Merge domainset and non_ip versions of a file.
    1. Collect entries from both domainset/{filename} and non_ip/{filename}
    2. Deduplicate (normalize by stripping known prefixes for comparison)
    3. Write unified file to folder root (data/YYYY-MM-DD/{output_filename})
    4. Remove source files if successful
    
    Returns True if successful, False otherwise.
    """
    domainset_conf = folder_path / "domainset" / source_filename
    non_ip_conf = folder_path / "non_ip" / source_filename
    output_conf = folder_path / output_filename
    
    # Check if at least one source exists
    sources_found = [p for p in [domainset_conf, non_ip_conf] if p.exists()]
    if not sources_found:
        print(f"  ⚠️ No source files found for {source_filename}")
        return False
    
    # Collect all entries, deduplicate by normalized domain
    entries_dict = {}  # normalized_domain -> original_line
    
    for source_path in sources_found:
        try:
            text = source_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  ⚠️ Failed to read {source_path.name}: {e}")
            continue
        
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            
            # Skip empty and comments
            if not stripped or stripped.startswith("#"):
                continue
            
            # Normalize: remove known prefixes to check for duplicates
            normalized = stripped
            for prefix in ["DOMAIN-SUFFIX,", "DOMAIN-KEYWORD,", "DOMAIN,", "URL-REGEX,", "DOMAIN-SET,", "DOMAIN-WILDCARD,"]:
                if normalized.startswith(prefix):
                    normalized = normalized[len(prefix):]
                    break
            
            # Store or skip if already seen (keep first occurrence)
            if normalized not in entries_dict:
                entries_dict[normalized] = raw_line
    
    if not entries_dict:
        print(f"  ⚠️ No valid entries found for {source_filename}")
        return False
    
    # Write merged file
    merged_lines = sorted(entries_dict.values())  # Sort for stable output
    output_conf.write_text("\n".join(merged_lines) + "\n", encoding="utf-8")
    print(f"  ✓ Merged {output_filename}: {len(merged_lines)} unique entries")
    
    # Remove source files if requested
    if remove_source:
        for source_path in sources_found:
            if source_path.exists():
                source_path.unlink()
                print(f"    → Removed {source_path.relative_to(folder_path.parent)}")
    
    return True


def main():
    today_folder = get_today_folder()
    if not today_folder.exists():
        print(f"❌ No folder found for today: {today_folder}")
        return
    
    print(f"\n📅 Processing snapshot for {today_folder.name}\n")
    
    # Step 1: Clean both domainset and non_ip folders
    print("Step 1: Cleaning files (removing markers, adding DOMAIN-SUFFIX,)\n")
    clean_and_process_files(today_folder / "domainset")
    clean_and_process_files(today_folder / "non_ip")
    
    # Step 2: Merge apple_cdn.conf
    print("\nStep 2: Merging apple_cdn.conf\n")
    merge_and_deduplicate_files(
        today_folder,
        source_filename="apple_cdn.conf",
        output_filename="Apple_CDN.conf",
        remove_source=True
    )
    
    # Step 3: Merge cdn.conf
    print("\nStep 3: Merging cdn.conf\n")
    merge_and_deduplicate_files(
        today_folder,
        source_filename="cdn.conf",
        output_filename="CDN.conf",
        remove_source=True
    )
    
    print("\n✅ All processing complete!\n")


if __name__ == "__main__":
    main()
