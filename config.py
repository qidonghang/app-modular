"""
config.py
---------
Default settings for the app.

Edit the values below to pre-fill fields every time the app opens.
"""

# ── Google Sheets URLs ────────────────────────────────────────────────────────
# Paste your Google Sheets URLs here (between the quotes).
# These pre-fill the Brand Judge / Brand Auth fields in the UI.
BRAND_JUDGE_URL = ""   # e.g. "https://docs.google.com/spreadsheets/d/XXXX/edit#gid=0"
BRAND_AUTH_URL  = ""   # e.g. "https://docs.google.com/spreadsheets/d/YYYY/edit#gid=0"

# ── Google Service Account Key ────────────────────────────────────────────────
# Path to the service account JSON key file.
# If set, the app uses the Google Sheets API (works with private sheets).
# If empty, the app falls back to public CSV export (sheet must be public).
#
# How to get one:
#   1. Go to console.cloud.google.com → create a project
#   2. Enable "Google Sheets API"
#   3. Create a Service Account → download the JSON key
#   4. Share your Google Sheets with the service account email (Viewer)
#   5. Paste the path to the JSON file below
SERVICE_ACCOUNT_KEY = ""   # e.g. "C:/Users/yourname/keys/sls-sorting-reader.json"
