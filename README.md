# HKMA Bank Disclosure Reader

Upload any HKMA Key Financial Information Disclosure Statement PDF and get a clean table of key metrics with period-over-period changes.

## What it extracts
- **Average LMR and CFR** — percentage-point change, year-over-year by quarter
- **Total assets and total liabilities** — % change, half-year
- **Specific, collective, and total provisions** — % change, half-year
- **Derivative financial liabilities**
- **Top 3 assets** and **top 3 liabilities** by concentration (as % of total)

---

## How to deploy on Streamlit Community Cloud (free — nothing to install on your Mac)

### Step 1 — Put the 4 files on GitHub
1. Go to github.com → click **New repository**
2. Name it `hkma-reader`, set it **Public**, click **Create repository**
3. On the next screen click **"uploading an existing file"**
4. Drag in all 4 files: `app.py`, `requirements.txt`, `packages.txt`, `README.md`
5. Click **Commit changes**

### Step 2 — Deploy
1. Go to **share.streamlit.io**, sign in with GitHub
2. Click **New app**
3. Pick your `hkma-reader` repo
4. Set **Main file path** → `app.py`
5. Click **Deploy**

Streamlit builds it automatically (~2 min). You get a live link you can open from any device.

**No terminal. No installs. Nothing on your Mac.**

---

## Troubleshooting

**"Could not find: Average LMR / CFR"** — The liquidity page is a scanned image. `packages.txt` installs Tesseract on Streamlit Cloud automatically. If it still fails, paste the error back.

**Numbers look off** — The app shows raw values on-screen before CSV export so you can verify. If something is wrong, it's usually a column alignment issue in that bank's specific PDF layout — easy to fix with a regex tweak.
