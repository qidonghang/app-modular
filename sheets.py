"""
sheets.py
---------
One job: download a public Google Sheet and return it as a pandas DataFrame.

How it works:
  1. Parse the spreadsheet ID from the URL  (the long code after /d/)
  2. Parse the sheet tab ID (gid=...)       (defaults to first tab if missing)
  3. Build a direct CSV download URL
  4. Read it with pandas
"""

import re
import pandas as pd


def fetch_sheet(url: str, name: str, log_fn=None) -> pd.DataFrame:
    """
    Download a public Google Sheet as a DataFrame.

    Parameters
    ----------
    url     : the full Google Sheets URL the user pasted
    name    : human-readable label used in log messages (e.g. "Brand Judge")
    log_fn  : optional function(msg, tag) for logging to the UI

    Returns
    -------
    pd.DataFrame on success, or None if URL is empty / download fails
    """
    def log(msg, tag=""):
        if log_fn:
            log_fn(msg, tag)

    url = url.strip()
    if not url:
        log(f"    {name}: no URL provided — skipped", "dim")
        return None

    try:
        # Extract the spreadsheet ID (always between /d/ and the next /)
        m_id = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if not m_id:
            raise ValueError("Cannot find spreadsheet ID in URL. Make sure you copied the full URL.")
        sid = m_id.group(1)

        # Extract the sheet tab ID (gid=...) — defaults to "0" (first tab)
        m_gid = re.search(r"[#&?]gid=([0-9]+)", url)
        gid = m_gid.group(1) if m_gid else "0"

        # Build the CSV export URL (this works for any public Google Sheet)
        csv_url = (
            f"https://docs.google.com/spreadsheets/d/{sid}"
            f"/export?format=csv&gid={gid}"
        )

        log(f"    Fetching {name} ...")
        df = pd.read_csv(csv_url, dtype=str)
        df.columns = df.columns.str.strip()
        log(f"    {name}: {len(df):,} rows  |  columns: {df.columns.tolist()}", "ok")
        return df

    except Exception as e:
        log(f"    {name} failed: {e}", "err")
        return None
