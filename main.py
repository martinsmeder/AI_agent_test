#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

import andon_labs_scraper
import openalex_scraper
import technologyreview_scraper

OUTPUT_DIR = Path("output")

SCRAPERS = [
    andon_labs_scraper,
    technologyreview_scraper,
    openalex_scraper,
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
    for scraper in SCRAPERS:
        name = scraper.__name__
        print(f"Running scraper: {name}")
        records = scraper.run()
        json_path, csv_path = write_output(records, scraper.FIELDS, scraper.OUTPUT_BASENAME)
        print(f"[{name}] Records: {len(records)}")
        print(f"[{name}] JSON: {json_path.resolve()}")
        print(f"[{name}] CSV:  {csv_path.resolve()}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
