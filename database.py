"""SQLite helper functions for storing and reading scraped data.

Fields vary by site, so rows are stored as JSON rather than fixed
columns — that's the one thing that has to change to support arbitrary
sites without a schema migration every time.
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = "data/scraped.db"


def init_db(db_path: str = DB_PATH) -> None:
    """Create the items table if it doesn't exist yet."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            scraped_at TEXT NOT NULL,
            data TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def insert_items(db_path: str, rows: list[dict]) -> None:
    """Insert scraped rows. Each row must include source_url and scraped_at;
    everything else is stored as JSON."""
    if not rows:
        return
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO items (source_url, scraped_at, data) VALUES (?, ?, ?)",
        [
            (
                row["source_url"],
                row["scraped_at"],
                json.dumps({k: v for k, v in row.items() if k not in ("source_url", "scraped_at")}),
            )
            for row in rows
        ],
    )
    conn.commit()
    conn.close()


def get_dataframe(db_path: str = DB_PATH) -> pd.DataFrame:
    """Load all scraped rows as a flat DataFrame — the JSON data column is
    expanded into regular columns so the dashboard can chart it."""
    if not Path(db_path).exists():
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    raw = pd.read_sql_query("SELECT source_url, scraped_at, data FROM items", conn)
    conn.close()
    if raw.empty:
        return raw
    fields = pd.json_normalize(raw["data"].apply(json.loads))
    return pd.concat([raw[["source_url", "scraped_at"]], fields], axis=1)
