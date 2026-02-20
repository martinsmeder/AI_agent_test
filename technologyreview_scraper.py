#!/usr/bin/env python3
import html
import re
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

FEED_URL = "https://www.technologyreview.com/feed/"
USER_AGENT = "Mozilla/5.0 (compatible; DataGatherer/1.0; +https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30

OUTPUT_BASENAME = "technologyreview_feed"
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


def run() -> list[dict[str, str]]:
    xml_text = _fetch_xml(FEED_URL)
    root = ET.fromstring(xml_text)

    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("Could not find RSS channel in Technology Review feed.")

    records: list[dict[str, str]] = []
    for item in channel.findall("item"):
        title = item.findtext("title", default="").strip()
        url = item.findtext("link", default="").strip()
        date = item.findtext("pubDate", default="").strip()

        content_node = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
        raw_content = content_node.text if content_node is not None and content_node.text else ""
        if not raw_content:
            raw_content = item.findtext("description", default="")

        content = _clean_text(raw_content)

        if not title or not url:
            continue

        records.append(
            {
                "title": _clean_text(title),
                "url": url,
                "date": date,
                "content": content,
            }
        )

    if not records:
        raise RuntimeError("No entries found in Technology Review RSS feed.")

    print(f"[technologyreview] Parsed {len(records)} feed items")
    return records
