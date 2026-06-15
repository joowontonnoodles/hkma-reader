# HKMA Bank Disclosure Reader v2

Extracts and compares key financial metrics from HKMA Key Financial Information Disclosure Statement PDFs.

## What it extracts 

| Metric | Comparison | Change type |
|--------|-----------|-------------|
| Average LMR | Q4 2025 vs Q4 2024 (YoY) | Percentage points |
| Average CFR | Q4 2025 vs Q4 2024 (YoY) | Percentage points |
| Total assets | 31-12-2025 vs 30-06-2025 (half-year) | % change |
| Total liabilities | 31-12-2025 vs 30-06-2025 (half-year) | % change |
| Specific provisions (loans) | half-year | % change |
| Collective provisions (loans) | half-year | % change |
| Total provisions (loans) | half-year | % change |
| Top 3 assets by concentration | current period | % of total assets |
| Top 3 liabilities by concentration | current period | % of total liabilities |

---

## Deploy on Streamlit Community Cloud (free — nothing to install on your Mac)

### Step 1 — Upload files to GitHub
1. Go to **github.com** → click **New repository**
2. Name it `hkma-reader`, set it **Public**, click **Create repository**
3. Click **"uploading an existing file"**
4. Drag in all 4 files: `app.py`, `requirements.txt`, `packages.txt`, `README.md`
5. Click **Commit changes**

### Step 2 — Deploy
1. Go to **share.streamlit.io** → sign in with GitHub
2. Click **New app**
3. Pick the `hkma-reader` repo
4. Set **Main file path** → `app.py`
5. Click **Deploy**

Builds in ~2 minutes. You get a live link, usable from any device.

**No terminal. No installs. Nothing on your Mac.**

---

## Troubleshooting

**LMR / CFR missing** — The liquidity page is a scanned image. Tesseract installs automatically via `packages.txt` on Streamlit Cloud. If it still fails, use the debug panel to see what raw text was extracted.

**A number looks wrong** — Use the "Show raw extracted text lines" debug panel at the bottom of the app to see exactly what the PDF produced. Paste the relevant lines back here and I can tighten the regex for that bank.
