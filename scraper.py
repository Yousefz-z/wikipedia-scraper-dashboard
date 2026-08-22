"""Wikipedia scraper for wikitables, infoboxes, and heading-filtered lists.

This is a library, not a CLI — dashboard.py is the only entry point.
"""
import io
import re
from datetime import datetime, timezone

import pandas as pd
import requests
from bs4 import BeautifulSoup

CURRENCY_CHARS = re.compile(r"[£$€,]")
CITATION_RE = re.compile(r"\s*\[[^\]]+\]")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; portfolio-scraper/1.0; educational project)"}


def _clean_text(value: str) -> str:
    return CITATION_RE.sub("", value).replace("\xa0", " ").strip()


def _maybe_number(value):
    """Convert '£51.77' -> 51.77, but leave anything that isn't purely
    numeric (once currency symbols/commas are stripped) as text."""
    if value is None:
        return None
    cleaned = _clean_text(value)
    stripped = CURRENCY_CHARS.sub("", cleaned).replace("%", "").strip()
    try:
        return float(stripped)
    except ValueError:
        return cleaned


def extract_field(item, spec: str):
    """Pull one field out of a BeautifulSoup item using a NAME=SELECTOR spec's selector half."""
    css_selector, _, attr = spec.partition("@")
    css_selector = css_selector.strip()

    target = item.select_one(css_selector) if css_selector else item
    if target is None:
        return None

    if attr:
        value = target.get(attr)
        if isinstance(value, list):  # e.g. a multi-valued "class" attribute
            value = " ".join(value)
    else:
        value = target.get_text(strip=True)

    return _maybe_number(value) if isinstance(value, str) else value


def parse_page(
    html: str | bytes, item_selector: str, fields: dict, source_url: str, scraped_at: str,
    heading_pattern: str | None = None,
) -> list[dict]:
    # Pass bytes rather than decoded text where possible — BeautifulSoup's
    # own encoding detection is more reliable than trusting a site's
    # (sometimes missing) Content-Type charset.
    soup = BeautifulSoup(html, "html.parser")
    heading_re = re.compile(heading_pattern) if heading_pattern else None

    rows = []
    for item in soup.select(item_selector):
        section = None
        if heading_re:
            heading = item.find_previous(["h1", "h2", "h3", "h4"])
            section = heading.get_text(strip=True) if heading else ""
            if not heading_re.search(section):
                continue

        if fields:
            row = {name: extract_field(item, spec) for name, spec in fields.items()}
        else:
            link = item.select_one("a")
            row = {
                "text": _maybe_number(item.get_text(" ", strip=True)),
                "link": link.get("href") if link else None,
            }
        if heading_re:
            row["section"] = section
        row["source_url"] = source_url
        row["scraped_at"] = scraped_at
        rows.append(row)
    return rows


def scrape_infobox(soup: BeautifulSoup, source_url: str, scraped_at: str) -> list[dict]:
    """Extract the first Wikipedia infobox as one key-value record."""
    infobox = soup.select_one("table.infobox")
    if infobox is None:
        return []

    row = {"source_url": source_url, "scraped_at": scraped_at}
    for table_row in infobox.select("tr"):
        label = table_row.find("th")
        value = table_row.find("td")
        if label is None or value is None:
            continue
        key = _clean_text(label.get_text(" ", strip=True))
        if key:
            row[key] = _maybe_number(value.get_text(" ", strip=True))

    return [row] if len(row) > 2 else []


def scrape_article_text(soup: BeautifulSoup, source_url: str, scraped_at: str) -> list[dict]:
    """Extract article paragraphs when structured Wikipedia data is unavailable."""
    content = soup.select_one("#mw-content-text") or soup.select_one(".mw-parser-output") or soup.select_one("main")
    if content is None:
        return []

    elements = content.select("p") or content.select("li")
    rows = []
    for element in elements:
        text = _clean_text(element.get_text(" ", strip=True))
        if text:
            rows.append({"text": text, "source_url": source_url, "scraped_at": scraped_at})
    return rows


def auto_scrape(
    url: str, mode: str = "Tables", heading_pattern: str | None = None,
) -> list[dict]:
    """Extract Wikipedia tables, infoboxes, heading-filtered lists, or article text."""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        print(f"Could not fetch {url} (status {resp.status_code})")
        return []

    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    soup = BeautifulSoup(resp.content, "html.parser")

    if mode == "Headings":
        rows = parse_page(
            resp.content,
            ".mw-parser-output li",
            {},
            url,
            scraped_at,
            heading_pattern,
        )
        return rows or scrape_article_text(soup, url, scraped_at)

    if mode == "Infobox":
        return scrape_infobox(soup, url, scraped_at) or scrape_article_text(soup, url, scraped_at)

    tables = []
    for table in soup.select("table.wikitable"):
        try:
            tables.extend(pd.read_html(io.StringIO(str(table)), flavor="lxml"))
        except (ValueError, ImportError):
            continue

    if tables:
        biggest = max(tables, key=len)
        rows = biggest.to_dict("records")
        for row in rows:
            for key, value in row.items():
                if isinstance(value, str):
                    row[key] = _maybe_number(value)
            row["source_url"] = url
            row["scraped_at"] = scraped_at
        print(f"Extracted Wikipedia wikitable with {len(rows)} rows. Columns: {list(biggest.columns)}")
        return rows

    print("No Wikipedia wikitables found; trying the article infobox and text.")
    return scrape_infobox(soup, url, scraped_at) or scrape_article_text(soup, url, scraped_at)
