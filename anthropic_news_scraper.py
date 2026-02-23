#!/usr/bin/env python3
import html
import re
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

FEED_URL = "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
USER_AGENT = "Mozilla/5.0 (compatible; DataGatherer/1.0; +https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30
WINDOW_DAYS = 30

OUTPUT_BASENAME = "anthropic_news_feed"
FIELDS = ["title", "url", "date", "content"]


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def _clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|li|h1|h2|h3|h4|h5|h6|tr|ul|ol|blockquote|section|article)>", "\n", text)
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


def _extract_article_content(article_html: str) -> str:
    html_text = article_html

    # Prefer the article region when available to avoid nav/footer text.
    article_start = html_text.lower().find("<article")
    if article_start != -1:
        article_end = html_text.lower().find("</article>", article_start)
        if article_end != -1:
            html_text = html_text[article_start : article_end + len("</article>")]
        else:
            html_text = html_text[article_start:]
    else:
        main_start = html_text.lower().find("<main")
        if main_start != -1:
            main_end = html_text.lower().find("</main>", main_start)
            if main_end != -1:
                html_text = html_text[main_start : main_end + len("</main>")]
            else:
                html_text = html_text[main_start:]

    html_text = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", html_text)
    html_text = re.sub(r"(?is)<!--.*?-->", " ", html_text)
    text = _clean_text(html_text)

    # Drop very short/empty parses so callers can choose a fallback.
    return text if len(text) >= 40 else ""


def run() -> list[dict[str, str]]:
    xml_text = _fetch_text(FEED_URL)
    root = ET.fromstring(xml_text)

    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("Could not find RSS channel in Anthropic news feed.")

    candidates: list[dict[str, str]] = []
    for item in channel.findall("item"):
        title = item.findtext("title", default="").strip()
        url = item.findtext("link", default="").strip()
        pub_date = item.findtext("pubDate", default="").strip()
        description = _clean_text(item.findtext("description", default=""))

        if not title or not url or not _in_last_window(pub_date):
            continue

        candidates.append(
            {
                "title": _clean_text(title),
                "url": url,
                "date": pub_date,
                "content": description,
            }
        )

    if not candidates:
        raise RuntimeError(f"No Anthropic news entries found in the last {WINDOW_DAYS} days.")

    records: list[dict[str, str]] = []
    for index, item in enumerate(candidates, start=1):
        print(f"[anthropic_news] [{index}/{len(candidates)}] Fetching content: {item['url']}")
        article_html = _fetch_text(item["url"])
        article_content = _extract_article_content(article_html)
        if article_content:
            item["content"] = article_content
        records.append(item)

    print(f"[anthropic_news] Parsed {len(records)} feed items from last {WINDOW_DAYS} days")
    return records
