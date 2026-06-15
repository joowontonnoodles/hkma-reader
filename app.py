import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# ── OCR support (used for scanned pages like the LMR/CFR page) ───────────────
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def to_num(s):
    """'(135,659)' → -135659.0    '354,199,518' → 354199518.0"""
    if not isinstance(s, str):
        return None
    s = s.strip().replace(",", "").replace(" ", "")
    s = re.sub(r"HK\$|'000|港幣千元|%", "", s)
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[()$]", "", s)
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None

def nums_from_row(row):
    """Return all numeric values found in a table row."""
    return [to_num(c) for c in row if to_num(c) is not None]

def nums_from_line(line):
    """Extract all numbers from a plain-text line."""
    tokens = re.findall(r"\([\d,]+(?:\.\d+)?\)|[\d,]+(?:\.\d+)?(?:\s*%)?", line)
    results = []
    for t in tokens:
        v = to_num(t.replace("%", ""))
        if v is not None:
            results.append(v)
    return results

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION: full text per page (reliable for this PDF layout)
# ─────────────────────────────────────────────────────────────────────────────

def extract_pages(pdf_bytes):
    """Return list of (page_index, text_lines, table_rows) for every page."""
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            rows = []
            for tbl in (page.extract_tables() or []):
                for row in tbl:
                    rows.append([c.strip() if isinstance(c, str) else (c or "") for c in row])
            pages.append((i, lines, rows))
    return pages

def ocr_text(pdf_bytes):
    if not OCR_AVAILABLE:
        return ""
    imgs = convert_from_bytes(pdf_bytes, dpi=200)
    return "\n".join(pytesseract.image_to_string(img) for img in imgs)

# ─────────────────────────────────────────────────────────────────────────────
# METRIC EXTRACTORS — each returns (current_val, prior_val) or None
# ─────────────────────────────────────────────────────────────────────────────

def find_two_nums_after(lines, pattern):
    """Scan lines; when pattern matches, return first two numbers on that line
    OR the two numbers found across that line + the next non-empty line."""
    for i, line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            nums = nums_from_line(line)
            if len(nums) >= 2:
                return nums[0], nums[1]
            # sometimes value sits on the next line
            for j in range(i+1, min(i+4, len(lines))):
                nums += nums_from_line(lines[j])
                if len(nums) >= 2:
                    return nums[0], nums[1]
    return None

def find_two_nums_in_rows(rows, pattern):
    """Search table rows for pattern; return first two numeric cells."""
    for row in rows:
        joined = " ".join(str(c) for c in row).lower()
        if re.search(pattern, joined):
            nums = nums_from_row(row)
            if len(nums) >= 2:
                return nums[0], nums[1]
    return None

def get_metric(lines, rows, pattern):
    """Try rows first, then plain text."""
    hit = find_two_nums_in_rows(rows, pattern)
    if hit:
        return hit
    hit = find_two_nums_after(lines, pattern)
    return hit

# ─────────────────────────────────────────────────────────────────────────────
# PROVISIONS — need context because "Collective" / "Specific" appear in multiple
# sections. We look specifically inside the balance-sheet impairment block.
# ─────────────────────────────────────────────────────────────────────────────

def get_provisions(all_lines):
    """
    In the balance sheet the structure is:
      Less: Impairment allowances for loans and advances
        - Collective   (135,659)   (191,635)
        - Specific     (144,525)   (145,789)
    We find that header then grab the next two labelled rows.
    """
    results = {"specific_loans": None, "collective_loans": None,
               "specific_other": None, "collective_other": None}

    in_loans_block = False
    in_other_block = False

    for line in all_lines:
        ll = line.lower()
        if re.search(r"impairment allowances for loans and advances", ll):
            in_loans_block = True
            in_other_block = False
            continue
        if re.search(r"impairment allowances for other claims", ll):
            in_other_block = True
            in_loans_block = False
            continue
        # exit blocks on next major section
        if re.search(r"total assets|total liabilities|liabilities", ll) and \
                not re.search(r"impairment|collective|specific|-", ll):
            in_loans_block = False
            in_other_block = False

        if in_loans_block or in_other_block:
            nums = nums_from_line(line)
            if len(nums) >= 2:
                if re.search(r"collective|組合", ll):
                    key = "collective_loans" if in_loans_block else "collective_other"
                    if results[key] is None:
                        results[key] = (abs(nums[0]), abs(nums[1]))
                elif re.search(r"specific|特定", ll):
                    key = "specific_loans" if in_loans_block else "specific_other"
                    if results[key] is None:
                        results[key] = (abs(nums[0]), abs(nums[1]))

    return results

# ─────────────────────────────────────────────────────────────────────────────
# LMR / CFR — live on a scanned page; try text first, then OCR
# ─────────────────────────────────────────────────────────────────────────────

def get_lmr_cfr(all_lines, pdf_bytes):
    lmr = find_two_nums_after(all_lines, r"average\s+lmr|liquidity maintenance ratio")
    cfr = find_two_nums_after(all_lines, r"average\s+cfr|core funding ratio")

    if not (lmr and cfr):
        raw = ocr_text(pdf_bytes)
        ocr_lines = [l.strip() for l in raw.splitlines() if l.strip()]
        if not lmr:
            lmr = find_two_nums_after(ocr_lines, r"average\s+lmr|lmr.*%")
        if not cfr:
            cfr = find_two_nums_after(ocr_lines, r"average\s+cfr|cfr.*%")
    return lmr, cfr

# ─────────────────────────────────────────────────────────────────────────────
# CONCENTRATION — rank balance-sheet line items by value, take top 3
# ─────────────────────────────────────────────────────────────────────────────

ASSET_ITEMS = [
    ("Amounts due from overseas offices",      r"amounts due from overseas offices"),
    ("Advances and other accounts",            r"advances and other accounts"),
    ("Securities held for trading",            r"securities held for trading"),
    ("Investment securities",                  r"investment securities"),
    ("Placements with banks (1-12m)",          r"placements with banks maturing"),
    ("Cash and balances with banks",           r"cash and balances with banks"),
    ("Certificates of deposit held",           r"certificates of deposit held"),
    ("Trade bills",                            r"trade bills"),
    ("Other investments",                      r"other investments"),
    ("Balances due from Exchange Fund",        r"balances due from exchange fund"),
    ("Property, plant and equipment",          r"property.*plant.*equipment"),
]

LIABILITY_ITEMS = [
    ("Time, call and notice deposits",         r"time.*call.*notice deposits"),
    ("Saving deposits",                        r"saving deposits"),
    ("Other accounts and provisions",          r"other accounts and provisions"),
    ("Deposits and balances from banks",       r"deposits and balances from banks"),
    ("Demand deposits / current accounts",     r"demand deposits and current accounts"),
    ("Amount due to overseas offices",         r"amount due to overseas offices"),
    ("Balances due to Exchange Fund",          r"balances due to exchange fund"),
    ("Amount payable under repo",              r"amount payable under repo"),
]

def get_concentration(lines, rows, items, total):
    found = []
    for label, pat in items:
        hit = get_metric(lines, rows, pat)
        if hit and total:
            curr = hit[0]
            found.append({"item": label, "value": curr,
                          "pct": round(abs(curr) / total * 100, 2)})
    found.sort(key=lambda x: abs(x["value"]), reverse=True)
    return found[:3]

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXTRACTION ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def run_extraction(pdf_bytes):
    pages = extract_pages(pdf_bytes)

    # Flatten all lines and rows across the whole document
    all_lines = []
    all_rows  = []
    for _, lines, rows in pages:
        all_lines.extend(lines)
        all_rows.extend(rows)

    records  = []
    warnings = []

    def add(metric, curr, prior, unit, comparison, change_type="pct"):
        if curr is None or prior is None:
            warnings.append(f"⚠️ Not found: {metric}")
            return
        if change_type == "pp":
            records.append({
                "Metric": metric, "Current": f"{curr}%", "Prior": f"{prior}%",
                "Abs Change": None, "% Change": None,
                "pp Change": round(curr - prior, 2),
                "Unit": unit, "Comparison": comparison,
            })
        else:
            abs_chg = round(curr - prior, 2)
            pct_chg = round((curr - prior) / abs(prior) * 100, 2) if prior else None
            records.append({
                "Metric": metric, "Current": curr, "Prior": prior,
                "Abs Change": abs_chg, "% Change": pct_chg,
                "pp Change": None,
                "Unit": unit, "Comparison": comparison,
            })

    # ── Total assets ──────────────────────────────────────────────────────────
    ta = get_metric(all_lines, all_rows, r"total\s+assets|總資產")
    add("Total assets", ta[0] if ta else None, ta[1] if ta else None,
        "HK$'000", "Half-year (31-12-2025 vs 30-06-2025)")

    # ── Total liabilities ─────────────────────────────────────────────────────
    tl = get_metric(all_lines, all_rows, r"total\s+liabilities|總負債")
    add("Total liabilities", tl[0] if tl else None, tl[1] if tl else None,
        "HK$'000", "Half-year (31-12-2025 vs 30-06-2025)")

    # ── Provisions ────────────────────────────────────────────────────────────
    prov = get_provisions(all_lines)

    sc = prov["specific_loans"]
    cc = prov["collective_loans"]
    add("Specific provisions (loans & advances)", sc[0] if sc else None, sc[1] if sc else None,
        "HK$'000", "Half-year (31-12-2025 vs 30-06-2025)")
    add("Collective provisions (loans & advances)", cc[0] if cc else None, cc[1] if cc else None,
        "HK$'000", "Half-year (31-12-2025 vs 30-06-2025)")

    if sc and cc:
        add("Total provisions (loans & advances)",
            sc[0] + cc[0], sc[1] + cc[1],
            "HK$'000", "Half-year (31-12-2025 vs 30-06-2025)")

    # ── LMR / CFR ─────────────────────────────────────────────────────────────
    lmr, cfr = get_lmr_cfr(all_lines, pdf_bytes)
    add("Average LMR", lmr[0] if lmr else None, lmr[1] if lmr else None,
        "%", "YoY – Q4 2025 vs Q4 2024", change_type="pp")
    add("Average CFR", cfr[0] if cfr else None, cfr[1] if cfr else None,
        "%", "YoY – Q4 2025 vs Q4 2024", change_type="pp")

    # ── Concentration ─────────────────────────────────────────────────────────
    total_assets = ta[0] if ta else None
    total_liab   = tl[0] if tl else None

    if total_assets:
        for i, a in enumerate(get_concentration(all_lines, all_rows, ASSET_ITEMS, total_assets), 1):
            records.append({
                "Metric": f"Top asset #{i}: {a['item']}",
                "Current": a["value"], "Prior": None,
                "Abs Change": None, "% Change": None, "pp Change": None,
                "Unit": "HK$'000",
                "Comparison": f"{a['pct']}% of total assets",
            })
    else:
        warnings.append("⚠️ Asset concentration skipped — total assets not found")

    if total_liab:
        for i, l in enumerate(get_concentration(all_lines, all_rows, LIABILITY_ITEMS, total_liab), 1):
            records.append({
                "Metric": f"Top liability #{i}: {l['item']}",
                "Current": l["value"], "Prior": None,
                "Abs Change": None, "% Change": None, "pp Change": None,
                "Unit": "HK$'000",
                "Comparison": f"{l['pct']}% of total liabilities",
            })
    else:
        warnings.append("⚠️ Liability concentration skipped — total liabilities not found")

    return pd.DataFrame(records), warnings, all_lines

# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="HKMA Disclosure Reader", layout="wide")
st.title("📊 HKMA Bank Disclosure Reader")
st.caption(
    "Upload a Key Financial Information Disclosure Statement PDF (HKMA format). "
    "Extracts key metrics and computes period-over-period changes automatically."
)

uploaded = st.file_uploader("Drop your HKMA PDF here", type="pdf")

if uploaded:
    pdf_bytes = uploaded.read()

    with st.spinner("Extracting data from PDF…"):
        df, warnings, raw_lines = run_extraction(pdf_bytes)

    # ── Warnings ──────────────────────────────────────────────────────────────
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} issue(s) — click to expand"):
            for w in warnings:
                st.write(w)

    if df.empty:
        st.error("Nothing extracted. The PDF may be fully scanned — make sure "
                 "Tesseract is installed (handled automatically on Streamlit Cloud).")
        st.stop()

    st.success(f"✅ Extracted {len(df)} metrics from **{uploaded.name}**")

    # ── Section 1: Liquidity ratios ───────────────────────────────────────────
    ratios = df[df["Metric"].str.startswith("Average")]
    if not ratios.empty:
        st.markdown("### Liquidity Ratios")
        st.caption("YoY comparison: Q4 2025 vs Q4 2024  |  Change shown in **percentage points (pp)**")
        st.dataframe(
            ratios[["Metric", "Current", "Prior", "pp Change", "Comparison"]],
            use_container_width=True, hide_index=True
        )

    # ── Section 2: Balance sheet & provisions ─────────────────────────────────
    balance = df[
        ~df["Metric"].str.startswith("Average") &
        ~df["Metric"].str.startswith("Top")
    ]
    if not balance.empty:
        st.markdown("### Balance Sheet & Provisions")
        st.caption("Half-year comparison: 31-12-2025 vs 30-06-2025  |  All values in HK$'000")
        st.dataframe(
            balance[["Metric", "Current", "Prior", "Abs Change", "% Change"]],
            use_container_width=True, hide_index=True
        )

    # ── Section 3: Concentration ──────────────────────────────────────────────
    conc = df[df["Metric"].str.startswith("Top")]
    if not conc.empty:
        st.markdown("### Asset & Liability Concentration (Top 3 each)")
        st.caption("Current period values only  |  Percentage = share of total assets or liabilities")
        st.dataframe(
            conc[["Metric", "Current", "Comparison"]],
            use_container_width=True, hide_index=True
        )

    # ── Download ──────────────────────────────────────────────────────────────
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️  Download full table as CSV",
        data=csv,
        file_name=f"hkma_{uploaded.name.replace('.pdf', '')}.csv",
        mime="text/csv",
    )

    # ── Debug panel ───────────────────────────────────────────────────────────
    with st.expander("🔍 Show raw extracted text lines (for debugging)"):
        st.text("\n".join(raw_lines[:300]))
