import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def to_num(s):
    if not isinstance(s, str):
        return None
    s = s.strip().replace(",", "").replace("HK$", "").replace("'000", "").replace("%", "")
    negative = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[()$\s]", "", s)
    try:
        v = float(s)
        return -v if negative else v
    except ValueError:
        return None

def find_in_rows(rows, pattern):
    for row in rows:
        text = " ".join(str(c) for c in row if c).lower()
        if re.search(pattern, text):
            nums = [to_num(c) for c in row if to_num(c) is not None]
            if nums:
                return nums
    return None

def extract_all_rows(pdf):
    rows = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for tbl in tables:
            for row in tbl:
                cleaned = [c.strip() if isinstance(c, str) else (c or "") for c in row]
                rows.append(cleaned)
    return rows

def ocr_all_text(pdf_bytes):
    if not OCR_AVAILABLE:
        return ""
    images = convert_from_bytes(pdf_bytes, dpi=200)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

def parse_lmr_cfr_from_text(text):
    results = {}
    patterns = {
        "lmr": r"average\s+lmr[^\d]*([\d.]+)\s*%[^\d]*([\d.]+)\s*%",
        "cfr": r"average\s+cfr[^\d]*([\d.]+)\s*%[^\d]*([\d.]+)\s*%",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            results[key] = (float(m.group(1)), float(m.group(2)))
    return results

FIELD_MAP = {
    "Total assets":                  {"pattern": r"total\s+assets",                                        "unit": "HK$'000", "type": "half-year"},
    "Total liabilities":             {"pattern": r"total\s+liabilities",                                   "unit": "HK$'000", "type": "half-year"},
    "Specific provisions (loans)":   {"pattern": r"specific.*impairment|specific\s*[-]\s*特定",            "unit": "HK$'000", "type": "half-year"},
    "Collective provisions (loans)": {"pattern": r"collective.*impairment|collective\s*[-]\s*組合",        "unit": "HK$'000", "type": "half-year"},
    "Derivative financial liab.":    {"pattern": r"fair\s+value\s+adjustment.*deriv|derivative.*financial","unit": "HK$'000", "type": "half-year"},
}

ASSETS = [
    ("Cash and balances with banks",       r"cash and balances with banks"),
    ("Balances due from Exchange Fund",     r"balances due from exchange fund"),
    ("Placements with banks (1-12m)",       r"placements with banks maturing"),
    ("Amounts due from overseas offices",   r"amounts due from overseas offices"),
    ("Trade bills",                         r"trade bills"),
    ("Certificates of deposit held",        r"certificates of deposit held"),
    ("Securities held for trading",         r"securities held for trading"),
    ("Advances and other accounts",         r"advances and other accounts"),
    ("Investment securities",               r"investment securities"),
    ("Other investments",                   r"other investments"),
    ("Property, plant and equipment",       r"property.*plant.*equipment"),
]

LIABILITIES = [
    ("Deposits and balances from banks",   r"deposits and balances from banks"),
    ("Balances due to Exchange Fund",       r"balances due to exchange fund"),
    ("Demand deposits / current accounts", r"demand deposits and current accounts"),
    ("Saving deposits",                     r"saving deposits"),
    ("Time, call and notice deposits",      r"time.*call.*notice deposits"),
    ("Amount due to overseas offices",      r"amount due to overseas offices"),
    ("Amount payable under repo",           r"amount payable under repo"),
    ("Other accounts and provisions",       r"other accounts and provisions"),
]

def concentration(rows, items, total):
    found = []
    for label, pat in items:
        hit = find_in_rows(rows, pat)
        if hit and total:
            val = hit[0]
            found.append({"item": label, "value": val, "pct": round(val / total * 100, 2)})
    found.sort(key=lambda x: abs(x["value"]), reverse=True)
    return found[:3]

def run_extraction(pdf_bytes):
    records, warnings = [], []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        rows = extract_all_rows(pdf)

    for field, cfg in FIELD_MAP.items():
        hit = find_in_rows(rows, cfg["pattern"])
        if hit and len(hit) >= 2:
            curr, prior = hit[0], hit[1]
            chg = round((curr - prior) / abs(prior) * 100, 2) if prior else None
            records.append({"Metric": field, "Current": curr, "Prior": prior,
                            "Abs Change": round(curr - prior, 2), "% Change": chg,
                            "pp Change": None, "Unit": cfg["unit"], "Comparison": cfg["type"]})
        else:
            warnings.append(f"Could not find: {field}")

    sp = next((r for r in records if r["Metric"] == "Specific provisions (loans)"), None)
    cp = next((r for r in records if r["Metric"] == "Collective provisions (loans)"), None)
    if sp and cp:
        tot_curr = sp["Current"] + cp["Current"]
        tot_prior = sp["Prior"] + cp["Prior"]
        records.append({"Metric": "Total provisions", "Current": round(tot_curr, 2),
                        "Prior": round(tot_prior, 2), "Abs Change": round(tot_curr - tot_prior, 2),
                        "% Change": round((tot_curr - tot_prior) / abs(tot_prior) * 100, 2),
                        "pp Change": None, "Unit": "HK$'000", "Comparison": "half-year"})

    lmr_hit = find_in_rows(rows, r"average\s+lmr|average.*liquidity.*maintenance")
    cfr_hit = find_in_rows(rows, r"average\s+cfr|average.*core.*funding")
    if not (lmr_hit and cfr_hit):
        parsed = parse_lmr_cfr_from_text(ocr_all_text(pdf_bytes))
        if "lmr" in parsed: lmr_hit = list(parsed["lmr"])
        if "cfr" in parsed: cfr_hit = list(parsed["cfr"])

    for label, hit in [("Average LMR", lmr_hit), ("Average CFR", cfr_hit)]:
        if hit and len(hit) >= 2:
            curr, prior = hit[0], hit[1]
            records.append({"Metric": label, "Current": f"{curr}%", "Prior": f"{prior}%",
                            "Abs Change": None, "% Change": None,
                            "pp Change": round(curr - prior, 2), "Unit": "%", "Comparison": "YoY (quarter)"})
        else:
            warnings.append(f"Could not find: {label}")

    ta = next((r for r in records if r["Metric"] == "Total assets"), None)
    tl = next((r for r in records if r["Metric"] == "Total liabilities"), None)

    if ta:
        for i, a in enumerate(concentration(rows, ASSETS, ta["Current"]), 1):
            records.append({"Metric": f"Top asset #{i}: {a['item']}", "Current": a["value"],
                            "Prior": None, "Abs Change": None, "% Change": None, "pp Change": None,
                            "Unit": "HK$'000", "Comparison": f"{a['pct']}% of total assets"})
    if tl:
        for i, l in enumerate(concentration(rows, LIABILITIES, tl["Current"]), 1):
            records.append({"Metric": f"Top liability #{i}: {l['item']}", "Current": l["value"],
                            "Prior": None, "Abs Change": None, "% Change": None, "pp Change": None,
                            "Unit": "HK$'000", "Comparison": f"{l['pct']}% of total liabilities"})

    return pd.DataFrame(records), warnings


st.set_page_config(page_title="HKMA Bank Disclosure Reader", layout="wide")
st.title("📊 HKMA Bank Disclosure Reader")
st.caption("Upload a Key Financial Information Disclosure Statement PDF from the HKMA.")

uploaded = st.file_uploader("Drop your HKMA PDF here", type="pdf")

if uploaded:
    pdf_bytes = uploaded.read()
    with st.spinner("Reading PDF and extracting data..."):
        df, warnings = run_extraction(pdf_bytes)

    if warnings:
        with st.expander(f"⚠️ {len(warnings)} field(s) not found — click to see"):
            for w in warnings:
                st.write(w)

    if not df.empty:
        st.success("Extraction complete!")
        ratios        = df[df["Metric"].str.startswith("Average")]
        balance       = df[~df["Metric"].str.startswith("Average") & ~df["Metric"].str.startswith("Top")]
        concentration = df[df["Metric"].str.startswith("Top")]

        if not ratios.empty:
            st.markdown("#### Liquidity Ratios (YoY — same quarter last year)")
            st.dataframe(ratios[["Metric","Current","Prior","pp Change","Comparison"]],
                         use_container_width=True, hide_index=True)

        if not balance.empty:
            st.markdown("#### Balance Sheet & Provisions (half-year: current vs 6 months ago)")
            st.dataframe(balance[["Metric","Current","Prior","Abs Change","% Change","Unit"]],
                         use_container_width=True, hide_index=True)

        if not concentration.empty:
            st.markdown("#### Asset & Liability Concentration (Top 3 each)")
            st.dataframe(concentration[["Metric","Current","Unit","Comparison"]],
                         use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download full table as CSV", data=csv,
                           file_name=f"hkma_{uploaded.name.replace('.pdf','')}.csv",
                           mime="text/csv")
    else:
        st.error("No data extracted. Make sure Tesseract is installed (see README).")
