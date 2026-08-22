#Wikipedia Scraper Dashboard

A Streamlit app that scrapes structured data straight out of any
Wikipedia article — no CSS selectors or command-line flags needed,
since Wikipedia's page structure is consistent enough to target
directly.

## How it works

```
dashboard.py (Streamlit UI) ──▶ scraper.py (extraction) ──▶ data/scraped.db (SQLite)
```

- **`dashboard.py`** — the only entry point. Enter an article URL, pick
  a mode, hit scrape, browse the results as a table.
- **`scraper.py`** — a small library with one function per extraction
  mode. No CLI; the dashboard calls it directly.
- **`database.py`** — stores each row's fields as JSON (since fields
  differ by mode and by article) and flattens them back into a table
  for display.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501`. Paste a Wikipedia article URL, choose
a mode, and click **Scrape Wikipedia page**:

- **Tables** — extracts the largest `wikitable` on the page (data
  tables, stats, lists of records), with column types inferred
  automatically. Good for articles like lists of countries, elections,
  sports results, etc.
- **Infobox** — extracts the summary box in the top-right of most
  articles (birth date, population, founding year...) as a single
  key/value record.
- **Headings** — collects list items (`<li>`) from the article body,
  filtered to only the sections whose heading matches a regular
  expression you provide (e.g. `^\d{4}$` for year-only headings). Useful
  for articles that group content under headings rather than tables.

If a mode doesn't find what it's looking for, it falls back to pulling
the article's plain paragraph text instead of returning nothing.

Every scrape is added to `data/scraped.db` rather than replacing what's
there, so you can build up a collection across multiple articles — the
dashboard shows items scraped, scrape runs, and source URLs scraped so
far, and filters the table to the article you just ran when there's a
match.

## Project structure

```
web-scraper-dashboard/
├── dashboard.py    # Streamlit UI — the entry point
├── scraper.py       # extraction logic (Tables / Infobox / Headings)
├── database.py       # SQLite read/write helpers
├── requirements.txt
├── data/              # SQLite DB lives here (gitignored)
└── README.md
```
