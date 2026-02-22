#!/usr/bin/env python3
import html
import json
import re
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OPENALEX_API_URL = "https://api.openalex.org/works"
SEARCH_QUERY = "artificial intelligence"
WINDOW_DAYS = 7
MAX_RESULTS = 200

USER_AGENT = "Mozilla/5.0 (compatible; DataGatherer/1.0; +https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30

OUTPUT_BASENAME = "openalex_api"
FIELDS = ["title", "url", "date", "content"]


def _clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _build_url() -> str:
    end_date = date.today()
    start_date = end_date - timedelta(days=WINDOW_DAYS - 1)
    params = {
        "search": SEARCH_QUERY,
        "filter": (
            f"from_publication_date:{start_date.isoformat()},"
            f"to_publication_date:{end_date.isoformat()}"
        ),
        "sort": "publication_date:desc",
        "per-page": MAX_RESULTS,
    }
    return f"{OPENALEX_API_URL}?{urlencode(params)}"


def _fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        text = response.read().decode("utf-8", errors="replace")
    return json.loads(text)


def _reconstruct_abstract(abstract_index: dict | None) -> str:
    if not abstract_index:
        return ""

    tokens_with_positions: list[tuple[int, str]] = []
    for token, positions in abstract_index.items():
        if not isinstance(token, str) or not isinstance(positions, list):
            continue
        for pos in positions:
            if isinstance(pos, int):
                tokens_with_positions.append((pos, token))

    if not tokens_with_positions:
        return ""

    tokens_with_positions.sort(key=lambda item: item[0])
    tokens = [token for _, token in tokens_with_positions]
    return _clean_text(" ".join(tokens))


def _parse_works(payload: dict) -> list[dict[str, str]]:
    works = payload.get("results", [])
    if not isinstance(works, list):
        return []
    records: list[dict[str, str]] = []

    for work in works:
        if not isinstance(work, dict):
            continue

        title = _clean_text(str(work.get("display_name", "") or ""))
        published = _clean_text(str(work.get("publication_date", "") or ""))

        primary_location = work.get("primary_location", {}) if isinstance(work.get("primary_location"), dict) else {}
        best_oa_location = work.get("best_oa_location", {}) if isinstance(work.get("best_oa_location"), dict) else {}

        entry_url = _clean_text(
            str(
                best_oa_location.get("landing_page_url")
                or primary_location.get("landing_page_url")
                or work.get("doi")
                or work.get("id")
                or ""
            )
        )
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

        if not title or not entry_url or not abstract:
            continue

        records.append(
            {
                "title": title,
                "url": entry_url,
                "date": published,
                "content": abstract,
            }
        )

    return records


def run() -> list[dict[str, str]]:
    url = _build_url()
    payload = _fetch_json(url)
    records = _parse_works(payload)

    if not records:
        raise RuntimeError("No entries found in OpenAlex response for the configured AI query.")

    print(f"[openalex] Parsed {len(records)} feed items from last {WINDOW_DAYS} days")
    return records
