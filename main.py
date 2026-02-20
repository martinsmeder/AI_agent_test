#!/usr/bin/env python3
import csv
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://andonlabs.com"
BLOG_INDEX_URL = f"{BASE_URL}/blog"
OUTPUT_DIR = Path("output")
OUTPUT_BASENAME = "andon_labs_blog"
USER_AGENT = "Mozilla/5.0 (compatible; AndonLabsBlogScraper/1.0; +https://example.local)"
REQUEST_TIMEOUT_SECONDS = 30

LISTING_PATTERN = re.compile(
    r'<article[^>]*>.*?<a href="([^"]+)"[^>]*>(.*?)</a>.*?<time>(.*?)</time>.*?</article>',
    re.DOTALL,
)

def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_blog_listing(blog_index_html: str) -> list[dict[str, str]]:
    posts: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for match in LISTING_PATTERN.finditer(blog_index_html):
        relative_url = match.group(1).strip()
        title = clean_text(re.sub(r"<[^>]+>", " ", match.group(2)))
        date = clean_text(match.group(3).strip())
        url = urljoin(BASE_URL, relative_url)

        if not title or url in seen_urls:
            continue

        seen_urls.add(url)
        posts.append({"title": title, "url": url, "date": date})

    return posts


def parse_article_content(article_html: str) -> str:
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
    return clean_text(text)


def write_outputs(posts: list[dict[str, str]]) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / f"{OUTPUT_BASENAME}.json"
    csv_path = OUTPUT_DIR / f"{OUTPUT_BASENAME}.csv"

    json_path.write_text(json.dumps(posts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=["title", "url", "date", "content"])
        writer.writeheader()
        writer.writerows(posts)

    return json_path, csv_path


def main() -> int:
    blog_index_html = fetch_html(BLOG_INDEX_URL)
    posts = parse_blog_listing(blog_index_html)

    if not posts:
        raise RuntimeError("No blog posts found. Blog page structure may have changed.")

    for index, post in enumerate(posts, start=1):
        print(f"[{index}/{len(posts)}] Fetching content: {post['url']}")
        article_html = fetch_html(post["url"])
        post["content"] = parse_article_content(article_html)

    json_path, csv_path = write_outputs(posts)

    print(f"Scraped {len(posts)} blog posts.")
    print(f"JSON: {json_path.resolve()}")
    print(f"CSV:  {csv_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
