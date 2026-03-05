# SLS Sorting Instruction Generator — Modular Version

> This folder is a **refactored** (reorganized) version of the original single-file app.
> The logic is identical — it's just split into smaller, easier-to-read files.

---

## What does this application do?

It takes Shopee SLS package data and automatically decides the **sorting instruction**
for each package: either keep the existing value, or change it to **HKP-F**.

- Packages from countries other than China → keep as-is, no changes
- Packages from China (CN) → run a brand check to decide CN or HKP-F

---

## Folder structure

```
app-modular/
│
├── main.py        ← START HERE. Launches the app window. (~10 lines)
├── ui.py          ← The window you see: buttons, text fields, log panel. (~200 lines)
├── processor.py   ← All the data logic: load Excel, merge, brand check, save. (~220 lines)
├── sheets.py      ← Downloads a Google Sheet and returns it as a table. (~50 lines)
└── README.md      ← This file
```

Think of it like a restaurant:
- `main.py` = the front door (you enter here)
- `ui.py` = the front-of-house staff (takes your order, shows you results)
- `processor.py` = the kitchen (does the actual cooking / data work)
- `sheets.py` = the delivery driver (fetches ingredients from Google Sheets)

---

## How the files talk to each other

```
main.py
  └── creates window → ui.py (SLSSortingApp)
                          │
                          │  when user clicks "Start Processing"
                          │
                          └── calls processor.run_processing()
                                  │
                                  ├── calls sheets.fetch_sheet()   (twice)
                                  ├── calls merge_manifest()
                                  └── calls apply_brand_routing()
```

Data only flows **downward**: `ui.py` calls `processor.py`, which calls `sheets.py`.
`sheets.py` never calls back up. This keeps things clean and easy to debug.

---

## How to run

### Prerequisites
Install the required Python packages once:
```
pip install pandas openpyxl
```

### Run the app
```
python main.py
```

---

## Step-by-step app usage

| Step | What to do |
|------|------------|
| 1 | Type the **Batch No.** (e.g. `PH-2026-03-001`) |
| 2 | Click **Browse** to select your **All Info** Excel file |
| 2 | Click **Browse** to select your **Manifest** Excel file |
| 3 | Paste the **Brand Judge** Google Sheets URL |
| 3 | Paste the **Brand Authorization** Google Sheets URL |
| 4 | Click **Browse** to choose where to save the output |
| — | Click **Start Processing** and watch the log |

Output file will be saved as: `Sorting Instruction of [Batch No].xlsx`

---

## What columns are needed in each input file?

### All Info Excel
| Column | Used for |
|--------|----------|
| `country` | Decide CN vs non-CN |
| `shipping_traceno` | Unique key per package |
| `ordersn_list` | Join to Manifest |
| `shopid` | Check brand authorization |
| `sorting_instruction` | Base value (may be overwritten to HKP-F) |
| `ordersn_list`, `consolidated_type`, `orderid`, `lm_tracking_number`, `cogs_sls`, `if_delivered`, `actual_weight`, `gp_account_name`, `child_account_name` | Copied to output |

### Manifest Excel
| Column | Used for |
|--------|----------|
| `ordersn` | Join key (matched to ordersn_list) |
| `item_name` | Brand keyword search |
| `sub_category` | Category exclusion check |
| `level3_category` | Category exclusion check |

### Brand Judge Google Sheet
| Column | Used for |
|--------|----------|
| `item name brand` | List of brand keywords to look for |
| `item name exclude` | If item_name also contains this → NOT HKP-F |
| `sub_cagtegory & level3_category exclue` | If category contains this → NOT HKP-F |

> Note: the column name `sub_cagtegory` has a typo — this is intentional,
> it matches the real column name in the Google Sheet.

### Brand Authorization Google Sheet
| Column | Used for |
|--------|----------|
| `child_shopid` | List of shop IDs that are authorized to sell the brand |

---

## CN Brand Routing Logic (plain English)

For each CN package, go through these checks in order:

```
1. Does item_name contain any brand from Brand Judge?
      No  →  Keep existing sorting_instruction (not a brand concern)
      Yes →  Continue to check 2

2. Does item_name also contain an "exclude" keyword?
      Yes →  Keep existing sorting_instruction (e.g. "Nike socks" might be excluded)
      No  →  Continue to check 3

3. Does sub_category or level3_category contain an "exclude" keyword?
      Yes →  Keep existing sorting_instruction
      No  →  Continue to check 4

4. Is the shopid in the Brand Authorization list?
      Yes →  Keep existing sorting_instruction (shop is licensed)
      No  →  Set to HKP-F  ← counterfeit risk
```

**After routing:** If any row on the same `shipping_traceno` becomes HKP-F,
ALL rows on that traceno also become HKP-F. One bad item = the whole parcel.

**Final step:** Keep only one row per `shipping_traceno` (dedup).

---

## Output columns (A to O)

| Column | Source |
|--------|--------|
| A: Batch no | Entered in Step 1 |
| B: shipping_traceno | All Info |
| C: ordersn_list | All Info |
| D: consolidated_type | All Info |
| E: orderid | All Info |
| F: lm_tracking_number | All Info |
| G: shopid | All Info |
| H: cogs_sls | All Info |
| I: if_delivered | All Info |
| J: actual_weight | All Info |
| K: gp_account_name | All Info |
| L: child_account_name | All Info |
| M: sorting_instruction | All Info (may be changed to HKP-F) |
| N: return_lm_tracking_number | Always blank |
| O: special remark | Always blank |

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `item_name` all blank | Manifest `ordersn` column not matching `ordersn_list` | Check for extra spaces or different formats |
| No HKP-F rows | Brand Judge URL not accessible | Make sure Google Sheet is set to "Anyone with the link can view" |
| `child_shopid` not found | Column name spelling differs | Check the exact column name in your Google Sheet |
| Google Sheets fetch fails | Sheet is not public | Open the sheet → Share → Change to "Anyone with the link" |
| `ModuleNotFoundError` when running | Missing packages | Run `pip install pandas openpyxl` |

---

## Should I use Git?

**Yes.** Even for a solo project. Git lets you save snapshots of your code so
you can always go back if something breaks.

### Recommended for beginners: GitHub Desktop
- Download: https://desktop.github.com
- It's a visual app — no need to type commands
- Steps:
  1. Install GitHub Desktop
  2. Click "Add an Existing Repository" → select this folder
  3. Write a short description of what you changed → click "Commit to main"
  4. Do this every time you make a meaningful change

**Rule of thumb:** commit whenever the app is in a working state —
before you start a new change, not after.
