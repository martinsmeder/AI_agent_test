#!/usr/bin/env python3
import html
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://andonlabs.com"
BLOG_INDEX_URL = f"{BASE_URL}/blog"
USER_AGENT = "Mozilla/5.0 (compatible; DataGatherer/1.0; +https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30
WINDOW_DAYS = 30

OUTPUT_BASENAME = "andon_labs_blog"
FIELDS = ["title", "url", "date", "content"]

LISTING_PATTERN = re.compile(
    r'<article[^>]*>.*?<a href="([^"]+)"[^>]*>(.*?)</a>.*?<time>(.*?)</time>.*?</article>',
    re.DOTALL,
)


def _fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def _clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_post_date(date_text: str) -> date | None:
    for fmt in ("%m/%d/%Y", "%-m/%-d/%Y"):
        try:
            return datetime.strptime(date_text, fmt).date()
        except ValueError:
            continue
    return None


def _in_last_window(date_text: str) -> bool:
    post_day = _parse_post_date(date_text)
    if post_day is None:
        return False

    end_day = date.today()
    start_day = end_day - timedelta(days=WINDOW_DAYS - 1)
    return start_day <= post_day <= end_day


def _parse_listing(blog_index_html: str) -> list[dict[str, str]]:
    posts: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for match in LISTING_PATTERN.finditer(blog_index_html):
        relative_url = match.group(1).strip()
        title = _clean_text(re.sub(r"<[^>]+>", " ", match.group(2)))
        date = _clean_text(match.group(3).strip())
        url = urljoin(BASE_URL, relative_url)

        if not title or url in seen_urls or not _in_last_window(date):
            continue

        seen_urls.add(url)
        posts.append({"title": title, "url": url, "date": date})

    return posts


def _parse_article_content(article_html: str) -> str:
    prose_index = article_html.find('class="prose')
    if prose_index != -1:
        div_start = article_html.rfind("<div", 0, prose_index)
        article_html = article_html[div_start if div_start != -1 else prose_index :]

    footer_index = article_html.find("<footer")
    if footer_index != -1:
        article_html = article_html[:footer_index]

    article_html = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", article_html)
    article_html = re.sub(r"(?is)<!--.*?-->", " ", article_html)
    article_html = re.sub(r"(?is)<br\s*/?>", "\n", article_html)
    article_html = re.sub(r"(?is)</(p|div|li|h1|h2|h3|h4|h5|h6|tr|ul|ol|blockquote)>", "\n", article_html)

    text = re.sub(r"(?is)<[^>]+>", " ", article_html)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return _clean_text(text)


def run() -> list[dict[str, str]]:
    blog_index_html = _fetch_html(BLOG_INDEX_URL)
    posts = _parse_listing(blog_index_html)

    if not posts:
        raise RuntimeError(f"No Andon Labs blog posts found in the last {WINDOW_DAYS} days.")

    for index, post in enumerate(posts, start=1):
        print(f"[andon_labs] [{index}/{len(posts)}] Fetching content: {post['url']}")
        article_html = _fetch_html(post["url"])
        post["content"] = _parse_article_content(article_html)

    print(f"[andon_labs] Parsed {len(posts)} posts from last {WINDOW_DAYS} days")
    return posts
