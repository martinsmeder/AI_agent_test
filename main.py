#!/usr/bin/env python3
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://andonlabs.com"
PUBLICATIONS_URL = f"{BASE_URL}/publications"
OUTPUT_DIR = Path("output")


def decode_js_string(raw: str) -> str:
    return (
        raw.replace("\\\\", "\\")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\r", "\r")
        .replace("\\t", "\t")
    )


def extract_from_hydration(html: str):
    block_match = re.search(r"items:\[(.*?)\],title:", html, re.DOTALL)
    if not block_match:
        return []

    items_block = block_match.group(1)
    item_pattern = re.compile(
        r'\{title:"((?:\\.|[^"\\])*)",date:(?:new Date\([^)]*\)|"[^"]*"),category:"((?:\\.|[^"\\])*)",link:"((?:\\.|[^"\\])*)"\}'
    )

    items = []
    for match in item_pattern.finditer(items_block):
        title = decode_js_string(match.group(1)).strip()
        category = decode_js_string(match.group(2)).strip()
        url = urljoin(BASE_URL, decode_js_string(match.group(3)).strip())

        if not title or not url:
            continue

        items.append({"title": title, "url": url, "category": category})

    return items


def unique_by_url(items):
    seen = set()
    deduped = []
    for item in items:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)
    return deduped


def fetch_html(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AndonLabsPublicationScraper/0.1; +https://example.local)"
        },
    )
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def write_outputs(items):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "publications.json"
    csv_path = OUTPUT_DIR / "publications.csv"

    json_path.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "category"])
        writer.writeheader()
        writer.writerows(items)

    return json_path, csv_path


def main():
    html = fetch_html(PUBLICATIONS_URL)
    scraped = unique_by_url(extract_from_hydration(html))

    if not scraped:
        raise RuntimeError("No publication entries found. Page structure may have changed.")

    json_path, csv_path = write_outputs(scraped)
    print(f"Scraped {len(scraped)} publications.")
    print(f"JSON: {json_path.resolve()}")
    print(f"CSV:  {csv_path.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
