import datetime
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent


def get_today_folder() -> Path:
    """
    Return today's snapshot folder: data/YYYY-MM-DD
    """
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return BASE_DIR / "data" / today


def remove_unwanted_strings(folder: Path):
    """
    Remove any line containing (case-insensitive):

      - '7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe'
      - 'this_ruleset_is_made_by_sukkaw.ruleset.skk.moe'
      - 'DOMAIN,this_ruleset_is_made_by_sukkaw.ruleset.skk.moe'
      - 'DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe'

    from files under these folders (relative to `folder`):

      - List/
      - Clash/
      - Surfboard/

    Only files with extensions:
      .conf, .txt, .json, .list, .yaml, .yml
    """

    markers = [
        "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
        "this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
    ]

    # Compile case-insensitive regex for each marker
    patterns = [re.compile(re.escape(m), re.IGNORECASE) for m in markers]

    target_folders = ["List", "Clash", "Surfboard"]

    processed_files = 0
    removed_lines_total = 0

    for sub in target_folders:
        base = folder / sub
        if not base.exists():
            print(f"Note: folder not found: {base}")
            continue

        for path in base.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in [".conf", ".txt", ".json", ".list", ".yaml", ".yml"]:
                continue

            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                print(f"Failed to read {path}: {e}")
                continue

            lines = text.splitlines()
            new_lines = []
            removed_here = 0

            for line in lines:
                # Remove line if any marker appears (case-insensitive)
                if any(p.search(line) for p in patterns):
                    removed_here += 1
                    continue
                new_lines.append(line)

            if removed_here > 0:
                path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                processed_files += 1
                removed_lines_total += removed_here
                rel = path.relative_to(folder)
                print(f"✓ Cleaned {rel}  (removed {removed_here} line(s))")

    print()
    print(f"Summary: {processed_files} file(s) modified, {removed_lines_total} line(s) removed.")


def main():
    today_folder = get_today_folder()
    if not today_folder.exists():
        print(f"No snapshot folder for today: {today_folder}")
        return

    print(f"Processing snapshot: {today_folder}")
    print("Target folders: List/, Clash/, Surfboard/")
    print()

    remove_unwanted_strings(today_folder)

    print("Done.")


if __name__ == "__main__":
    main()