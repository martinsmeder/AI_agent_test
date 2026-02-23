# news_aggregator

Simple Python news scraper/aggregator that collects recent AI-related posts from multiple sources and writes a single combined output.

## What It Does

- Scrapes multiple AI/news sources
- Filters results to the last month (rolling 30-day window, inclusive)
- Extracts `title`, `url`, `date`, and `content`
- Combines all successful scraper results into one shared output
- Continues running even if one or more scrapers fail

## Current Sources

- Andon Labs blog
- MIT Technology Review (AI topic RSS)
- OpenAI News RSS
- Google DeepMind blog RSS
- Anthropic news (RSS mirror + article page fetch for full content)
- xAI news (news index + article page fetch for full content)

## Output

Running the script writes:

- `output/combined_feed.json`
- `output/combined_feed.csv`

Each record uses this schema:

- `title`
- `url`
- `date`
- `content`

## How To Run

Requirements:

- Python 3.10+ (tested with system `python3`)
- Internet access (the scrapers fetch live pages/RSS feeds)

Run:

```bash
python3 main.py
```

## Behavior Notes

- The date filter is applied inside each scraper using a rolling 30-day window based on the local machine date.
- Some sources are RSS-only (content usually comes from RSS description/encoded content).
- Anthropic and xAI scrapers first collect links/dates, filter to the last month, then fetch only the matching article pages to reduce load.
- If all scrapers fail, the script exits with a non-zero status code.
- If at least one scraper succeeds, combined output is still written.

## Project Structure

- `main.py`: orchestrates scrapers and writes combined output
- `*_scraper.py`: one scraper per source
- `output/`: generated JSON/CSV files
