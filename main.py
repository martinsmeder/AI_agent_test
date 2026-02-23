#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

import anthropic_news_scraper
import andon_labs_scraper
import deepmind_blog_scraper
import openai_news_scraper
import technologyreview_scraper

OUTPUT_DIR = Path("output")
COMBINED_OUTPUT_BASENAME = "combined_feed"

SCRAPERS = [
    andon_labs_scraper,
    technologyreview_scraper,
    openai_news_scraper,
    deepmind_blog_scraper,
    anthropic_news_scraper,
]


def write_output(records: list[dict[str, str]], fields: list[str], basename: str) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / f"{basename}.json"
    csv_path = OUTPUT_DIR / f"{basename}.csv"

    json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    return json_path, csv_path


def main() -> int:
    had_any_success = False
    combined_records: list[dict[str, str]] = []
    combined_fields = andon_labs_scraper.FIELDS

    for scraper in SCRAPERS:
        name = scraper.__name__
        print(f"Running scraper: {name}")
        try:
            records = scraper.run()
            print(f"[{name}] Records: {len(records)}")
            combined_records.extend(records)
            had_any_success = True
        except Exception as exc:
            print(f"[{name}] ERROR: {exc}", file=sys.stderr)
            continue

    if had_any_success:
        json_path, csv_path = write_output(combined_records, combined_fields, COMBINED_OUTPUT_BASENAME)
        print(f"[combined] Records: {len(combined_records)}")
        print(f"[combined] JSON: {json_path.resolve()}")
        print(f"[combined] CSV:  {csv_path.resolve()}")

    return 0 if had_any_success else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
