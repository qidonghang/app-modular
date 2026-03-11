"""
processor.py
------------
All data processing logic — no GUI code here.

Three functions, called in order by run_processing():
  1. merge_manifest()      — joins All Info + Manifest Excel files
  2. apply_brand_routing() — decides CN vs HKP-F for each package
  3. run_processing()      — the main pipeline: load → merge → route → save
"""

import os
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from sheets import fetch_sheet


# ── Module-level constants ─────────────────────────────────────────────────────

# The required output columns in order (A to M before the two blank columns)
OUTPUT_COLS = [
    "shipping_traceno", "ordersn_list", "consolidated_type",
    "orderid", "lm_tracking_number", "shopid", "cogs_sls",
    "if_delivered", "actual_weight", "gp_account_name",
    "child_account_name", "sorting_instruction",
]


# ── Shared utilities ───────────────────────────────────────────────────────────

def _log(msg: str, tag: str, log_fn) -> None:
    """Send a message to the UI log panel. Does nothing if log_fn is None."""
    if log_fn:
        log_fn(msg, tag)


def _norm_id(x) -> str:
    """
    Normalize a shop ID or order ID to a plain integer string.
    e.g.  "12345.0"  →  "12345"
          "12345"    →  "12345"
    """
    try:
        return str(int(float(str(x).strip())))
    except Exception:
        return str(x).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Step A: Merge the two Excel files
# ─────────────────────────────────────────────────────────────────────────────

def merge_manifest(ai: pd.DataFrame, mnf: pd.DataFrame, log_fn=None) -> pd.DataFrame:
    """
    Join All Info (ai) with Manifest (mnf).

    Why this is needed:
      - All Info has one row per package (shipping_traceno), with a single orderid.
      - Manifest may have MULTIPLE rows per orderid (one per item in the order),
        with item details (item_name, sub_category, level3_category).
      - We need item details to run the brand check across ALL items in the order.
      - The join intentionally produces multiple rows per shipping_traceno when
        an order has multiple items. Brand routing checks every item row, and
        run_processing() deduplicates back to one row per shipping_traceno afterwards.

    Join key: All Info.orderid  ←→  Manifest.orderid
    """
    # Guard: make sure both sides have the join column
    if "orderid" not in ai.columns or "orderid" not in mnf.columns:
        _log("    orderid column missing in All Info or Manifest — skipping merge", "warn", log_fn)
        return ai.copy()

    # Keep only the columns we actually need from Manifest
    mnf_cols = [c for c in ["orderid", "item_name", "sub_category", "level3_category"]
                if c in mnf.columns]
    mnf_sub = mnf[mnf_cols].dropna(subset=["orderid"]).copy()
    mnf_sub["orderid"] = mnf_sub["orderid"].str.strip()

    # Drop any manifest columns that already exist in ai (to avoid duplicates)
    detail_cols = [c for c in ["item_name", "sub_category", "level3_category"]
                   if c in mnf_sub.columns]
    ai_clean = ai.drop(columns=[c for c in detail_cols if c in ai.columns], errors="ignore")

    # Left join on orderid.
    # NOTE: Manifest may have multiple rows per orderid (multiple items in one order).
    # In that case, the All Info row is duplicated — one copy per Manifest item.
    # Brand routing will check ALL copies, so if any item triggers HKP-F the
    # shipping_traceno is flagged. The dedup step in run_processing() then
    # collapses them back to one row per shipping_traceno (HKP-F kept first).
    result = ai_clean.merge(mnf_sub, on="orderid", how="left")

    # Report how many rows ended up with no item_name (unmatched orders)
    no_item = result.get("item_name", pd.Series(dtype=str)).isna().sum()
    if no_item:
        _log(f"    {no_item:,} rows have no item_name after merge (orderid not in Manifest)", "warn", log_fn)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Step B: CN Brand Routing
# ─────────────────────────────────────────────────────────────────────────────

def apply_brand_routing(df: pd.DataFrame, bj_df, ba_df, log_fn=None) -> pd.DataFrame:
    """
    For every CN-origin row, decide: keep existing sorting_instruction or set HKP-F.

    Decision tree (per row):
      - Non-CN package         → pass through unchanged
      - CN, no brand match     → keep as-is
      - CN, brand match BUT item_name contains an exclude keyword → keep as-is
      - CN, brand match BUT category contains an exclude keyword  → keep as-is
      - CN, brand match + shopid is authorized                    → keep as-is
      - CN, brand match + shopid NOT authorized                   → HKP-F

    Parameters
    ----------
    df    : merged DataFrame (output of merge_manifest)
    bj_df : Brand Judge sheet (or None if not provided)
    ba_df : Brand Authorization sheet (or None if not provided)
    """
    # ── Parse Brand Judge sheet ──────────────────────────────────────────────
    brand_terms = []   # list of brand keywords to search in item_name
    item_excl   = []   # item_name keywords that cancel a brand hit
    cat_excl    = []   # category keywords that cancel a brand hit

    if bj_df is not None:
        bj = bj_df.copy()
        bj.columns = bj.columns.str.strip()

        def _find_col(cols, keyword):
            """Find a column whose name contains the given keyword (case-insensitive)."""
            return next((c for c in cols if keyword.lower() in c.lower()), None)

        c_brand = _find_col(bj.columns, "item name brand")
        c_iexcl = _find_col(bj.columns, "item name exclude")
        c_cexcl = _find_col(bj.columns, "sub_category")

        if c_brand:
            brand_terms = bj[c_brand].dropna().str.strip().tolist()
            preview = brand_terms[:5]
            suffix = "..." if len(brand_terms) > 5 else ""
            _log(f"    Brands ({len(brand_terms)}): {preview}{suffix}", "info", log_fn)

        if c_iexcl:
            item_excl = bj[c_iexcl].dropna().str.strip().tolist()
            preview = item_excl[:4]
            suffix = "..." if len(item_excl) > 4 else ""
            _log(f"    Item name excludes ({len(item_excl)}): {preview}{suffix}", "", log_fn)

        if c_cexcl:
            for cell in bj[c_cexcl].dropna().str.strip():
                cat_excl.extend([t.strip() for t in re.split(r"[,;|、\n]+", cell) if t.strip()])
            preview = cat_excl[:4]
            suffix = "..." if len(cat_excl) > 4 else ""
            _log(f"    Category excludes ({len(cat_excl)}): {preview}{suffix}", "", log_fn)

    # ── Parse Brand Authorization sheet ─────────────────────────────────────
    auth_ids: set = set()

    if ba_df is not None:
        ba = ba_df.copy()
        ba.columns = ba.columns.str.strip()
        sc = next((c for c in ba.columns if "child_shopid" in c.lower()), None)
        if sc:
            auth_ids = set(ba[sc].dropna().apply(_norm_id))
            _log(f"    Authorized shop IDs: {len(auth_ids):,}", "info", log_fn)
        else:
            _log("    Brand Auth: column 'child_shopid' not found", "warn", log_fn)

    # ── Split: only rows with sorting_instruction == "CN" get brand routing ──
    is_cn = df.get("sorting_instruction", pd.Series(dtype=str)).str.strip().str.upper() == "CN"
    _log(f"    Pass-through (not CN): {(~is_cn).sum():,}", "", log_fn)
    _log(f"    Brand check (CN)     : {is_cn.sum():,}", "", log_fn)

    if not is_cn.any():
        return df  # nothing CN, nothing to do

    cn = df[is_cn].copy()

    # Text columns used for matching
    si = cn.get("item_name",       pd.Series("", index=cn.index)).fillna("").astype(str)
    ss = cn.get("sub_category",    pd.Series("", index=cn.index)).fillna("").astype(str)
    sl = cn.get("level3_category", pd.Series("", index=cn.index)).fillna("").astype(str)

    sid_norm = cn.get("shopid", pd.Series("", index=cn.index)).apply(_norm_id)

    # Build regex patterns once (faster than per-row string searching)
    ie_pat = ("|".join(re.escape(t) for t in item_excl)) if item_excl else None
    ce_pat = ("|".join(re.escape(t) for t in cat_excl))  if cat_excl  else None

    # hkp_mask: True for rows that will become HKP-F
    hkp_mask = pd.Series(False, index=cn.index)

    # Check each brand independently (a row is HKP-F if ANY brand triggers it)
    for brand in brand_terms:
        if not brand:
            continue

        # Does item_name contain this brand?
        hit = si.str.contains(re.escape(brand), case=False, na=False)
        if not hit.any():
            continue

        # Is this hit cancelled by an exclusion rule?
        excl = pd.Series(False, index=cn.index)
        if ie_pat:
            excl |= hit & si.str.contains(ie_pat, case=False, na=False)
        if ce_pat:
            excl |= hit & (ss.str.contains(ce_pat, case=False, na=False) |
                           sl.str.contains(ce_pat, case=False, na=False))

        # Hit + not excluded + not an authorized shop → HKP-F
        hkp_mask |= hit & (~excl) & (~sid_norm.isin(auth_ids))

    cn.loc[hkp_mask, "sorting_instruction"] = "HKP-F"

    _log(f"    CN rows kept as-is : {(~hkp_mask).sum():,}", "ok", log_fn)
    _log(f"    CN rows → HKP-F   : {int(hkp_mask.sum()):,}", "ok", log_fn)

    # Recombine non-CN and CN rows
    return pd.concat([df[~is_cn], cn], ignore_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_processing(params: dict, log_fn=None) -> dict:
    """
    Full processing pipeline. Called by the UI when the user clicks Start.

    Parameters
    ----------
    params : dict with keys:
        batch_no        — text entered in Step 1
        all_info_path   — path to All Info Excel file
        manifest_path   — path to Manifest Excel file
        brand_judge_url — Google Sheets URL or local file (Brand Judge)
        brand_auth_url  — Google Sheets URL or local file (Brand Authorization)
        out_dir         — folder where the output file will be saved

    Returns
    -------
    dict with keys: out_path, out_fname, rows, hkp_f, out_dir
    """
    batch_no  = params["batch_no"]
    out_dir   = params["out_dir"]
    out_fname = f"Sorting Instruction of {batch_no}.xlsx"
    out_path  = os.path.join(out_dir, out_fname)

    _log("=" * 65, "dim", log_fn)
    _log("  SortFlow — SLS Sorting Instruction Generator", "info", log_fn)
    _log("=" * 65, "dim", log_fn)
    _log(f"Batch No : {batch_no}", "info", log_fn)
    _log(f"Output   : {out_fname}", "info", log_fn)

    # 1+2/5 — Load All Info and Manifest in parallel (both are independent)
    _log("\n[1/5]  Loading Excel files (parallel) ...", "", log_fn)
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_ai  = ex.submit(pd.read_excel, params["all_info_path"],  sheet_name=0, engine="openpyxl")
        f_mnf = ex.submit(pd.read_excel, params["manifest_path"], sheet_name=0, engine="openpyxl")
        all_info = f_ai.result().astype(str).replace("nan", "")
        manifest = f_mnf.result().astype(str).replace("nan", "")

    all_info.columns = all_info.columns.str.strip()
    manifest.columns = manifest.columns.str.strip()

    # Keep only the output columns from All Info — discard everything else immediately
    ai_keep    = [c for c in OUTPUT_COLS if c in all_info.columns]
    ai_missing = [c for c in OUTPUT_COLS if c not in all_info.columns]
    if ai_missing:
        _log(f"    Missing columns in All Info: {ai_missing}", "warn", log_fn)
    all_info = all_info[ai_keep]

    # Split immediately: non-CN rows are set aside and never touched again
    is_cn  = all_info["sorting_instruction"].str.strip().str.upper() == "CN"
    non_cn  = all_info[~is_cn].copy()   # locked — goes straight to output
    cn_only = all_info[is_cn].copy()    # will be merged, routed, deduped

    cn_count = is_cn.sum()
    _log(f"    All Info — Rows: {len(all_info):,}  |  sorting=CN: {cn_count:,}  |  Other: {len(non_cn):,}", "ok", log_fn)
    _log(f"    Manifest — Rows: {len(manifest):,}", "ok", log_fn)

    missing_mnf = [c for c in ["orderid", "item_name", "sub_category", "level3_category"]
                   if c not in manifest.columns]
    if missing_mnf:
        _log(f"    Missing columns in Manifest: {missing_mnf}", "warn", log_fn)

    # 3/5 — Fetch Brand sheets in parallel (both are independent)
    _log("\n[3/5]  Fetching brand data (parallel) ...", "", log_fn)
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_bj = ex.submit(fetch_sheet, params["brand_judge_url"], "Brand Judge",        log_fn)
        f_ba = ex.submit(fetch_sheet, params["brand_auth_url"],  "Brand Authorization", log_fn)
        brand_judge_df = f_bj.result()
        brand_auth_df  = f_ba.result()

    # 4/5 — Merge CN rows with Manifest only
    _log("\n[4/5]  Merging CN rows with Manifest ...", "", log_fn)
    merged_cn = merge_manifest(cn_only, manifest, log_fn)
    _log(f"    sorting=CN after merge: {len(merged_cn):,} rows  (Others untouched: {len(non_cn):,})", "ok", log_fn)

    # 5/5 — Brand routing on CN rows only
    _log("\n[5/5]  Applying CN brand routing ...", "", log_fn)
    routed_cn = apply_brand_routing(merged_cn, brand_judge_df, brand_auth_df, log_fn)

    # Dedup CN rows: one row per shipping_traceno.
    # Sort HKP-F rows first within each traceno — so if ANY item in the order
    # triggers HKP-F, the kept row reflects that result.
    before = len(routed_cn)
    si_col = routed_cn.get("sorting_instruction", pd.Series("", index=routed_cn.index))
    routed_cn = (
        routed_cn
        .assign(_hkp_first=(si_col != "HKP-F").astype(int))
        .sort_values(["shipping_traceno", "_hkp_first"])
        .drop(columns=["_hkp_first"])
        .drop_duplicates(subset=["shipping_traceno"], keep="first")
    )
    _log(f"\nDedup CN rows: {before:,} → {len(routed_cn):,}", "ok", log_fn)

    # Drop Manifest-only columns (item_name, sub_category, level3_category) from CN rows
    # so both halves have identical columns before concat
    routed_cn = routed_cn[ai_keep]

    # Recombine: non-CN rows (unchanged) + deduped CN rows
    result = pd.concat([non_cn, routed_cn], ignore_index=True)
    _log(f"Final rows (non-CN + CN): {len(result):,}", "ok", log_fn)

    result["return_lm_tracking_number"] = ""   # always blank per spec
    result["special remark"]            = ""   # always blank per spec
    result.insert(0, "Batch no", batch_no)     # Column A

    result.to_excel(out_path, index=False, sheet_name="Sheet1")

    hkp_f = int((result["sorting_instruction"] == "HKP-F").sum())
    _log("\n" + "=" * 65, "dim", log_fn)
    _log(f"DONE  |  Rows: {len(result):,}  |  HKP-F: {hkp_f:,}", "ok", log_fn)
    _log(f"Saved → {out_fname}", "ok", log_fn)
    _log("=" * 65, "dim", log_fn)

    return {
        "out_path":  out_path,
        "out_fname": out_fname,
        "rows":      len(result),
        "hkp_f":     hkp_f,
        "out_dir":   out_dir,
    }
