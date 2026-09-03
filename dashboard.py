"""
Streamlit dashboard for the Wikipedia scraper — pick an extraction mode
(table, infobox, or heading-filtered list), enter an article URL, and
browse whatever comes back.

Run with:  streamlit run dashboard.py
"""

import re
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st

from database import DB_PATH, get_dataframe, init_db, insert_items
from scraper import auto_scrape


def is_valid_wikipedia_url(url: str) -> bool:
    """True when url is an http(s) address on wikipedia.org or a language subdomain."""
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        return False
    hostname = parsed_url.hostname or ""
    return hostname == "wikipedia.org" or hostname.endswith(".wikipedia.org")


def collect_inputs() -> tuple[str, str, str | None]:
    """Draw the input controls and return the URL, mode, and heading pattern."""
    article_url = st.text_input(
        "Wikipedia URL",
        placeholder="https://en.wikipedia.org/wiki/Albert_Einstein",
    )
    mode = st.radio("Extraction mode", ("Tables", "Infobox", "Headings"), horizontal=True)

    heading_pattern = None
    if mode == "Headings":
        heading_pattern = st.text_input(
            "Heading regular expression",
            placeholder=r"History",
            help="Only list items under headings matching this expression will be collected.",
        )

    return article_url, mode, heading_pattern


def scrape_and_store(target_url: str, mode: str, heading_pattern: str | None) -> None:
    """Scrape one article, store the rows it produced, and report any failure."""
    try:
        with st.spinner("Scraping the page…"):
            rows = auto_scrape(target_url, mode=mode, heading_pattern=heading_pattern)
    except requests.Timeout:
        st.error(
            "Wikipedia took longer than 10 seconds to respond. Check your connection and try again."
        )
        return
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "an error"
        st.error(
            f"Wikipedia returned HTTP {status} for that URL. "
            "Check that the article exists and the address is spelled correctly."
        )
        return
    except requests.ConnectionError:
        st.error("Could not reach Wikipedia. Check your internet connection and try again.")
        return
    except requests.RequestException as exc:
        st.error(f"The request to Wikipedia could not be completed: {exc}")
        return
    except re.error as exc:
        st.error(
            f"That heading regular expression is not valid ({exc}). "
            "Try a plain word such as History, or escape any special characters."
        )
        return

    if not rows:
        st.warning("The scraper did not find any usable data rows on that page.")
        return

    init_db(DB_PATH)
    insert_items(DB_PATH, rows)
    st.rerun()


def handle_scrape_request(article_url: str, mode: str, heading_pattern: str | None) -> None:
    """Reject unusable input with a message, otherwise run the scrape."""
    target_url = article_url.strip()

    if not target_url:
        st.warning("Enter a Wikipedia URL before starting a scrape.")
    elif not is_valid_wikipedia_url(target_url):
        st.error(
            "Enter a valid Wikipedia URL, such as https://en.wikipedia.org/wiki/Albert_Einstein."
        )
    elif mode == "Headings" and not heading_pattern:
        st.warning("Enter a heading regular expression before scraping list items.")
    else:
        scrape_and_store(target_url, mode, heading_pattern)


def render_results(df: pd.DataFrame, article_url: str) -> None:
    """Show the summary metrics and the scraped rows, filtered to the current article."""
    if df.empty:
        st.warning("No data yet. Enter a Wikipedia URL above to collect data.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Items scraped", len(df))
    col2.metric("Scrape runs", df["scraped_at"].nunique())
    col3.metric("Source URLs", df["source_url"].nunique())

    display_df = df.sort_values("scraped_at", ascending=False)
    current_url_rows = display_df[display_df["source_url"] == article_url.strip()]
    if not current_url_rows.empty:
        display_df = current_url_rows

    st.subheader("Scraped data")
    st.dataframe(display_df.dropna(axis=1, how="all"), hide_index=True)


def main() -> None:
    """Draw the whole page, top to bottom."""
    st.set_page_config(page_title="Wikipedia Data Scraper Dashboard", layout="wide")
    st.title("Wikipedia Data Scraper Dashboard")

    article_url, mode, heading_pattern = collect_inputs()

    if st.button("Scrape Wikipedia page", type="primary"):
        handle_scrape_request(article_url, mode, heading_pattern)

    render_results(get_dataframe(DB_PATH), article_url)


if __name__ == "__main__":
    main()
