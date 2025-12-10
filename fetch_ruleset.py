import os
import sys
import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://ruleset.skk.moe"


def get_today_folder():
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return os.path.join("data", today)


def fetch_index():
    resp = requests.get(BASE_URL, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_file_links(html):
    """
    Parse all file links listed on the main page.
    Only keep direct links (no anchors starting with '#').
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []

    # The site is a simple list; just grab all <a> with href that looks like a file.
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        # Skip in-page anchors and external links
        if href.startswith("#"):
            continue
        if href.startswith("http://") or href.startswith("https://"):
            # Only keep if same host
            if href.startswith(BASE_URL):
                links.append(href)
            continue
        # Relative path on this site
        full_url = urljoin(BASE_URL + "/", href)
        links.append(full_url)

    # De-duplicate
    links = sorted(set(links))
    return links


def save_file(url, base_folder):
    rel_path = url.replace(BASE_URL, "").lstrip("/")
    if not rel_path:
        return

    target_path = os.path.join(base_folder, rel_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    print(f"Downloading {url} -> {target_path}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    # Save as binary to be safe
    with open(target_path, "wb") as f:
        f.write(resp.content)


def main():
    base_folder = get_today_folder()
    os.makedirs(base_folder, exist_ok=True)

    html = fetch_index()
    links = parse_file_links(html)

    # Optionally filter to certain extensions; currently keep all discovered files
    for url in links:
        # Skip the index itself
        if url.rstrip("/") == BASE_URL.rstrip("/"):
            continue
        try:
            save_file(url, base_folder)
        except Exception as e:
            print(f"Failed to download {url}: {e}", file=sys.stderr)

    print("Done.")


if __name__ == "__main__":
    main()

