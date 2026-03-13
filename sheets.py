"""
sheets.py
---------
Load brand data as a pandas DataFrame — from a Google Sheets URL or a local file.

Three modes (auto-detected):
  1. Google Sheets URL + service account JSON  → authenticated API read (private sheets OK)
  2. Google Sheets URL (no key file)           → public CSV export (legacy fallback)
  3. Local file path                           → read .xlsx / .xls / .csv directly from disk
"""

import os
import re
import pandas as pd

# Lazy-initialized gspread client (created once, reused for all sheets)
_gspread_client = None


def _get_gspread_client(key_data):
    """Create (or reuse) a gspread client from embedded dict or JSON file path."""
    global _gspread_client
    if _gspread_client is None and key_data:
        import gspread
        if isinstance(key_data, dict):
            _gspread_client = gspread.service_account_from_dict(key_data)
        elif isinstance(key_data, str) and os.path.isfile(key_data):
            _gspread_client = gspread.service_account(filename=key_data)
    return _gspread_client


def fetch_sheet(url_or_path: str, name: str, log_fn=None,
                sa_key_data=None) -> pd.DataFrame:
    """
    Load a sheet as a DataFrame — from a Google Sheets URL or a local file.

    Parameters
    ----------
    url_or_path : Google Sheets URL  — fetched from the web
                  OR a local file path (.xlsx / .xls / .csv) — read directly
    name        : human-readable label for log messages (e.g. "Brand Judge")
    log_fn      : optional function(msg, tag) for logging to the UI
    sa_key_data : service account credentials — dict (embedded) or file path string

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

        # Try authenticated path first (service account)
        gc = _get_gspread_client(sa_key_data)

        if gc:
            log(f"    Fetching {name} via Service Account ...")
            sh = gc.open_by_url(value)

            # Find the right tab by gid (from the URL)
            m_gid = re.search(r"[#&?]gid=([0-9]+)", value)
            target_gid = int(m_gid.group(1)) if m_gid else 0
            ws = next(
                (w for w in sh.worksheets() if w.id == target_gid),
                sh.sheet1,
            )

            records = ws.get_all_records()
            df = pd.DataFrame(records).astype(str)
        else:
            # Legacy path: public CSV export (no auth)
            sid = m_id.group(1)
            m_gid = re.search(r"[#&?]gid=([0-9]+)", value)
            gid = m_gid.group(1) if m_gid else "0"
            csv_url = (
                f"https://docs.google.com/spreadsheets/d/{sid}"
                f"/export?format=csv&gid={gid}"
            )
            log(f"    Fetching {name} from Google Sheets (public CSV, no key) ...")
            df = pd.read_csv(csv_url, dtype=str)

        df.columns = df.columns.str.strip()
        log(f"    {name}: {len(df):,} rows  |  columns: {df.columns.tolist()}", "ok")
        return df

    except Exception as e:
        log(f"    {name} failed: {e}", "err")
        return None
