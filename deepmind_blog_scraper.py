#!/usr/bin/env python3
import html
import re
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

FEED_URL = "https://deepmind.google/blog/rss.xml"
USER_AGENT = "Mozilla/5.0 (compatible; DataGatherer/1.0; +https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30
WINDOW_DAYS = 30

OUTPUT_BASENAME = "deepmind_blog_feed"
FIELDS = ["title", "url", "date", "content"]


def _fetch_xml(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def _clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|li|h1|h2|h3|h4|h5|h6|tr|ul|ol|blockquote)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _in_last_window(pub_date_text: str) -> bool:
    if not pub_date_text:
        return False

    try:
        pub_dt = parsedate_to_datetime(pub_date_text)
    except (TypeError, ValueError):
        return False

    pub_day = pub_dt.date()
    end_day = date.today()
    start_day = end_day - timedelta(days=WINDOW_DAYS - 1)
    return start_day <= pub_day <= end_day


def run() -> list[dict[str, str]]:
    xml_text = _fetch_xml(FEED_URL)
    root = ET.fromstring(xml_text)

    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("Could not find RSS channel in DeepMind blog feed.")

    records: list[dict[str, str]] = []
    for item in channel.findall("item"):
        title = item.findtext("title", default="").strip()
        url = item.findtext("link", default="").strip()
        pub_date = item.findtext("pubDate", default="").strip()

        raw_content = item.findtext("description", default="")
        content = _clean_text(raw_content)

        if not title or not url or not _in_last_window(pub_date):
            continue

        records.append(
            {
                "title": _clean_text(title),
                "url": url,
                "date": pub_date,
                "content": content,
            }
        )

    if not records:
        raise RuntimeError("No entries found in DeepMind blog RSS feed.")

    print(f"[deepmind_blog] Parsed {len(records)} feed items from last {WINDOW_DAYS} days")
    return records
