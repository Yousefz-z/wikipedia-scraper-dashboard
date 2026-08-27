"""
Streamlit dashboard for the Wikipedia scraper — pick an extraction mode
(table, infobox, or heading-filtered list), enter an article URL, and
browse whatever comes back.

Run with:  streamlit run dashboard.py
"""
import re
from urllib.parse import urlparse

import requests
import streamlit as st

from database import DB_PATH, get_dataframe, init_db, insert_items
from scraper import auto_scrape

st.set_page_config(page_title="Wikipedia Data Scraper Dashboard", layout="wide")
st.title("Wikipedia Data Scraper Dashboard")

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

if st.button("Scrape Wikipedia page", type="primary"):
    target_url = article_url.strip()
    parsed_url = urlparse(target_url)

    if not target_url:
        st.warning("Enter a Wikipedia URL before starting a scrape.")
    elif parsed_url.scheme not in ("http", "https") or not (
        parsed_url.hostname == "wikipedia.org"
        or (parsed_url.hostname or "").endswith(".wikipedia.org")
    ):
        st.error("Enter a valid Wikipedia URL, such as https://en.wikipedia.org/wiki/Albert_Einstein.")
    elif mode == "Headings" and not heading_pattern:
        st.warning("Enter a heading regular expression before scraping list items.")
    else:
        try:
            with st.spinner("Scraping the page…"):
                rows = auto_scrape(target_url, mode=mode, heading_pattern=heading_pattern)

            if rows:
                init_db(DB_PATH)
                insert_items(DB_PATH, rows)
                st.rerun()
            else:
                st.warning("The scraper did not find any usable data rows on that page.")
        except requests.Timeout:
            st.error(
                "Wikipedia took longer than 10 seconds to respond. "
                "Check your connection and try again."
            )
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "an error"
            st.error(
                f"Wikipedia returned HTTP {status} for that URL. "
                "Check that the article exists and the address is spelled correctly."
            )
        except requests.ConnectionError:
            st.error("Could not reach Wikipedia. Check your internet connection and try again.")
        except requests.RequestException as exc:
            st.error(f"The request to Wikipedia could not be completed: {exc}")
        except re.error as exc:
            st.error(
                f"That heading regular expression is not valid ({exc}). "
                "Try a plain word such as History, or escape any special characters."
            )

df = get_dataframe(DB_PATH)

if df.empty:
    st.warning("No data yet. Enter a Wikipedia URL above to collect data.")
else:
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
