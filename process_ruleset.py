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
        "DOMAIN,this_ruleset_is_made_by_sukkaw