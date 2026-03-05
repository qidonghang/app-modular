"""
sheets.py
---------
Load brand data as a pandas DataFrame — from a Google Sheets URL or a local file.

Two modes (auto-detected):
  1. Google Sheets URL  → parse spreadsheet ID + tab ID, fetch as CSV
  2. Local file path    → read .xlsx / .xls / .csv directly from disk
"""

import os
import re
import pandas as pd


def fetch_sheet(url_or_path: str, name: str, log_fn=None) -> pd.DataFrame:
    """
    Load a sheet as a DataFrame — from a Google Sheets URL or a local file.

    Parameters
    ----------
    url_or_path : Google Sheets URL  — fetched from the web
                  OR a local file path (.xlsx / .xls / .csv) — read directly
    name        : human-readable label for log messages (e.g. "Brand Judge")
    log_fn      : optional function(msg, tag) for logging to the UI

    Returns
    -------
    pd.DataFrame on success, or None if input is empty / loading fails
    """
    def log(msg, tag=""):
        if log_fn:
            log_fn(msg, tag)

    value = url_or_path.strip()
    if not value:
        log(f"    {name}: not provided — skipped", "dim")
        return None

    # ── Local file fallback ──────────────────────────────────────────────────
    if os.path.isfile(value):
        try:
            log(f"    {name}: reading local file ...")
            ext = os.path.splitext(value)[1].lower()
            if ext in (".xlsx", ".xls"):
                df = pd.read_excel(value, dtype=str)
            else:
                df = pd.read_csv(value, dtype=str)
            df.columns = df.columns.str.strip()
            log(f"    {name}: {len(df):,} rows  |  columns: {df.columns.tolist()}", "ok")
            return df
        except Exception as e:
            log(f"    {name} local file failed: {e}", "err")
            return None

    # ── Google Sheets URL ────────────────────────────────────────────────────
    try:
        m_id = re.search(r"/d/([a-zA-Z0-9_-]+)", value)
        if not m_id:
            raise ValueError("Not a valid Google Sheets URL and not a local file path.")
        sid = m_id.group(1)

        m_gid = re.search(r"[#&?]gid=([0-9]+)", value)
        gid = m_gid.group(1) if m_gid else "0"

        csv_url = (
            f"https://docs.google.com/spreadsheets/d/{sid}"
            f"/export?format=csv&gid={gid}"
        )

        log(f"    Fetching {name} from Google Sheets ...")
        df = pd.read_csv(csv_url, dtype=str)
        df.columns = df.columns.str.strip()
        log(f"    {name}: {len(df):,} rows  |  columns: {df.columns.tolist()}", "ok")
        return df

    except Exception as e:
        log(f"    {name} failed: {e}", "err")
        return None
