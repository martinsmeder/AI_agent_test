#!/usr/bin/env python3
import html
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://x.ai"
NEWS_URL = f"{BASE_URL}/news"
USER_AGENT = "Mozilla/5.0 (compatible; DataGatherer/1.0; +https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30
WINDOW_DAYS = 30

OUTPUT_BASENAME = "xai_news_feed"
FIELDS = ["title", "url", "date", "content"]

LINK_PATTERN = re.compile(r'<a[^>]+href="(/news/[^"#?]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
DATE_PATTERN = re.compile(r"\b([A-Z][a-z]+ \d{2}, \d{4})\b")


def _fetch_html(url: str) -> str:
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


def _parse_xai_date(date_text: str) -> date | None:
    try:
        return datetime.strptime(date_text, "%B %d, %Y").date()
    except ValueError:
        return None


def _in_last_window(date_text: str) -> bool:
    published_day = _parse_xai_date(date_text)
    if published_day is None:
        return False
    end_day = date.today()
    start_day = end_day - timedelta(days=WINDOW_DAYS - 1)
    return start_day <= published_day <= end_day


def _find_nearest_date(html_text: str, anchor_index: int) -> str:
    window_start = max(0, anchor_index - 1200)
    window_end = min(len(html_text), anchor_index + 1200)
    window = html_text[window_start:window_end]

    best_date = ""
    best_distance = 10**9
    for match in DATE_PATTERN.finditer(window):
        distance = abs((window_start + match.start()) - anchor_index)
        if distance < best_distance:
            best_distance = distance
            best_date = match.group(1)
    return best_date


def _parse_listing(news_html: str) -> list[dict[str, str]]:
    posts: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for match in LINK_PATTERN.finditer(news_html):
        relative_url = match.group(1).strip()
        if relative_url == "/news":
            continue

        title = _clean_text(match.group(2))
        if not title or title.upper() == "READ":
            continue

        url = urljoin(BASE_URL, relative_url)
        if url in seen_urls:
            continue

        date_text = _find_nearest_date(news_html, match.start())
        if not date_text or not _in_last_window(date_text):
            continue

        seen_urls.add(url)
        posts.append({"title": title, "url": url, "date": date_text})

    if not posts:
        return []

    # Preserve newest-first ordering if the page is in descending order; regex scan order already follows page order.
    return posts


def _extract_article_content(article_html: str) -> str:
    html_text = article_html
    lower = html_text.lower()

    article_start = lower.find("<article")
    if article_start != -1:
        article_end = lower.find("</article>", article_start)
        html_text = html_text[article_start : article_end + len("</article>")] if article_end != -1 else html_text[article_start:]
    else:
        main_start = lower.find("<main")
        if main_start != -1:
            main_end = lower.find("</main>", main_start)
            html_text = html_text[main_start : main_end + len("</main>")] if main_end != -1 else html_text[main_start:]

    html_text = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", html_text)
    html_text = re.sub(r"(?is)<!--.*?-->", " ", html_text)
    text = _clean_text(html_text)

    # Trim obvious site chrome if present after article content.
    for marker in ("Try Grok On", "Products", "Resources", "Privacy policy"):
        marker_index = text.find(marker)
        if marker_index > 0:
            text = text[:marker_index].strip()
            break

    return text


def run() -> list[dict[str, str]]:
    news_html = _fetch_html(NEWS_URL)
    posts = _parse_listing(news_html)

    if not posts:
        raise RuntimeError(f"No xAI news posts found in the last {WINDOW_DAYS} days.")

    for index, post in enumerate(posts, start=1):
        print(f"[xai_news] [{index}/{len(posts)}] Fetching content: {post['url']}")
        article_html = _fetch_html(post["url"])
        post["content"] = _extract_article_content(article_html)

    print(f"[xai_news] Parsed {len(posts)} posts from last {WINDOW_DAYS} days")
    return posts
