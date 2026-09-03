"""
Entry point for the Wikipedia scraper app. Sets the page configuration and
routes between views; each view lives in its own module under views/.

Run with:  streamlit run app.py
"""

import streamlit as st

from views import articles, dashboard, settings


def main() -> None:
    """Configure the page, then hand control to whichever view is selected."""
    st.set_page_config(page_title="Wikipedia Data Scraper Dashboard", layout="wide")

    pages = [
        st.Page(dashboard.render, title="Dashboard", url_path="dashboard", default=True),
        st.Page(articles.render, title="Articles", url_path="articles"),
        st.Page(settings.render, title="Settings", url_path="settings"),
    ]
    st.navigation(pages).run()


if __name__ == "__main__":
    main()
