
import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import io, re, os
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="HKMA Financial Disclosure Analyser", layout="wide", page_icon="🏦")

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #f0f2f6; }

.hero {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px; padding: 36px 40px 28px; margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.hero h1 { color: #fff; font-size: 2rem; font-weight: 700; margin: 0 0 6px 0; letter-spacing: -0.5px; }
.hero p  { color: rgba(255,255,255,0.65); font-size: 0.95rem; margin: 0; }

.card {
    background: #fff; border-radius: 12px; padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 20px;
}
.card-title { font-size: 0.7rem; font-weight: 600; letter-spacing: 1.2px;
              text-transform: uppercase; color: #6b7280; margin-bottom: 4px; }
.card-value { font-size: 1.6rem; font-weight: 700; color: #111827; }
.card-sub   { font-size: 0.8rem; color: #6b7280; margin-top: 2px; }
.badge-up   { display:inline-block; background:#dcfce7; color:#166534;
              font-size:0.72rem; font-weight:600; padding:2px 8px;
              border-radius:20px; margin-left:8px; }
.badge-dn   { display:inline-block; background:#fee2e2; color:#991b1b;
              font-size:0.72rem; font-weight:600; padding:2px 8px;
              border-radius:20px; margin-left:8px; }
.badge-nt   { display:inline-block; background:#f3f4f6; color:#374151;
              font-size:0.72rem; font-weight:600; padding:2px 8px;
              border-radius:20px; margin-left:8px; }

.section-header {
    font-size: 1.05rem; font-weight: 700; color: #111827;
    border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin: 28px 0 16px;
}
.info-box {
    background: #eff6ff; border-left: 4px solid #3b82f6;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    font-size: 0.875rem; color: #1e40af; margin-bottom: 16px;
}
.warn-box {
    background: #fffbeb; border-left: 4px solid #f59e0b;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    font-size: 0.875rem; color: #92400e; margin-bottom: 16px;
}
.entity-header {
    background: linear-gradient(135deg, #1a1a2e, #0f3460);
    border-radius: 12px; padding: 22px 28px; margin-bottom: 20px;
    color: white;
}
.entity-header h2 { margin: 0; font-size: 1.5rem; font-weight: 700; }
.entity-header .meta { font-size: 0.85rem; opacity: 0.7; margin-top: 4px; }

table.styled { width:100%; border-collapse:collapse; font-size:0.875rem; }
table.styled th {
    background:#1a1a2e; color:#fff; padding:10px 14px;
    text-align:left; font-weight:600; font-size:0.8rem; letter-spacing:0.3px;
}
table.styled td { padding:9px 14px; border-bottom:1px solid #f3f4f6; color:#374151; }
table.styled tr:last-child td { border-bottom:none; }
table.styled tr:hover td { background:#f9fafb; }
.num { text-align:right !important; font-variant-numeric: tabular-nums; }
.bold-row td { font-weight:700; color:#111827 !important; background:#f9fafb; }
</style>
""", unsafe_allow_html=True)

# ─── HERO ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🏦 HKMA Financial Disclosure Analyser</h1>
    <p>Upload any HKMA Banking Disclosure PDF — branches, locally incorporated banks, restricted licence banks</p>
</div>
""", unsafe_allow_html=True)

# ─── HELPERS ────────────────────────────────────────────────────────────────────

def extract_text(uploaded_file) -> str:
    """Extract text from PDF, falling back to OCR page by page."""
    text_pages = []
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if len(t.strip()) < 40:          # likely scanned
                img = page.to_image(resolution=200).original
                t = pytesseract.image_to_string(img)
            text_pages.append(t)
    return "
".join(text_pages)


JUNK = re.compile(r"""
    ^(key\s+financial|financial\s+information|disclosure|statements?|
      contents?|chief\s+executive|declaration|notes?\s+to|
      as\s+at|for\s+the\s+(year|period)|pages?|
      GROUPE|BPCE|KPMG|FOR\s+IDENTIFICATION|ONLY|
      HONG\s+KONG\s*$|incorporated\s+in|liability\s+of|
      with\s+limited|unaudited|audited|section\s+[a-z]|
      limited\s+liability|法國|香港|the\s+company|
      CORPORATE\s+AND|INVESTMENT\s+BANKING|
      AND\s+INVESTMENT\s+BANKING|
      stamp|signature|\[|\d+\s*$)
""", re.IGNORECASE | re.VERBOSE)


def extract_entity_name(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Pass 1: look for a line containing "Hong Kong Branch" near the top (first 80 lines)
    for line in lines[:80]:
        if re.search(r"hong\s+kong\s+branch", line, re.IGNORECASE):
            name = re.sub(r"\s+", " ", line).strip()
            # remove trailing Chinese text or parentheticals
            name = re.split(r"\s{2,}|法國|（|[）(]incorporated", name, flags=re.IGNORECASE)[0].strip()
            if len(name) > 4:
                return name

    # Pass 2: look for entity name patterns without "Hong Kong Branch"
    for line in lines[:40]:
        if len(line) < 5 or JUNK.match(line):
            continue
        # Skip if looks like a subtitle
        if re.match(r"^(CORPORATE|INVESTMENT|GROUP|GROUPE|BPCE|KPMG)", line, re.IGNORECASE):
            continue
        words = line.split()
        if len(words) >= 2 and line[0].isupper():
            return line

    return "Unknown Institution"


def parse_num(s: str):
    """Parse numeric string, handling parentheses = negative, dashes = 0."""
    s = str(s).strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "—", "–", "N/A", "n/a"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def find_value(text: str, patterns: list, window: int = 160):
    """Return first numeric value found after any of the regex patterns."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            snippet = text[m.end(): m.end() + window]
            # find next standalone number (possibly in parens)
            nm = re.search(r"[\(\-]?\s*[\d,]+(?:\.\d+)?[\)]?", snippet)
            if nm:
                v = parse_num(nm.group())
                if v is not None:
                    return v
    return None


def find_two_values(text: str, patterns: list, window: int = 220):
    """Return (current, prior) pair after a pattern."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            snippet = text[m.end(): m.end() + window]
            nums = re.findall(r"[\(\-]?\s*[\d,]+(?:\.\d+)?[\)]?", snippet)
            parsed = [parse_num(n) for n in nums if parse_num(n) is not None]
            if len(parsed) >= 2:
                return parsed[0], parsed[1]
            if len(parsed) == 1:
                return parsed[0], None
    return None, None


def detect_unit(text: str):
    """Return multiplier: 1 for unit, 1000 for thousands, 1_000_000 for millions."""
    t = text[:3000]
    if re.search(r"in\s+(thousands?|HK\$?\s*thousands?|HKD\s*thousands?|港幣千元)", t, re.IGNORECASE):
        return 1_000, "HKD thousands"
    if re.search(r"in\s+(millions?|HK\$?\s*millions?|HKD\s*millions?|US\$?\s*millions?)", t, re.IGNORECASE):
        return 1_000_000, "millions"
    if re.search(r"US\$?\s*US\$", t):
        return 1, "USD"
    # check for large raw numbers (>= 8 digits suggests unit)
    big = re.findall(r"\d{8,}", t)
    if big:
        return 1, "units"
    return 1_000_000, "millions"  # default


def detect_currency(text: str):
    t = text[:2000]
    if re.search(r"US\s*\$|USD|United States dollars?", t, re.IGNORECASE) and        not re.search(r"HKD|Hong Kong dollar", t[:500], re.IGNORECASE):
        return "USD"
    return "HKD"


def fmt(val, unit_mult, decimals=1):
    if val is None:
        return "N/A"
    actual = val * unit_mult
    if abs(actual) >= 1e12:
        return f"{actual/1e12:,.{decimals}f}T"
    if abs(actual) >= 1e9:
        return f"{actual/1e9:,.{decimals}f}B"
    if abs(actual) >= 1e6:
        return f"{actual/1e6:,.{decimals}f}M"
    return f"{actual:,.0f}"


def chg(curr, prev, pct=False):
    if curr is None or prev is None:
        return "N/A", "nt"
    if pct:
        d = curr - prev
        s = f"{d:+.1f}pp"
    else:
        if prev == 0:
            return "N/M", "nt"
        d = (curr - prev) / abs(prev) * 100
        s = f"{d:+.1f}%"
    cls = "up" if d > 0 else ("dn" if d < 0 else "nt")
    return s, cls


def badge(val, cls):
    css = {"up": "badge-up", "dn": "badge-dn", "nt": "badge-nt"}
    return f'<span class="{css.get(cls,"badge-nt")}">{val}</span>'


# ─── MAIN EXTRACTION ────────────────────────────────────────────────────────────

def extract_all(text: str) -> dict:
    unit_mult, unit_label = detect_unit(text)
    currency = detect_currency(text)
    entity = extract_entity_name(text)

    # ── Reporting date ──────────────────────────────────────────────────────────
    date_m = re.search(
        r"(?:as\s+(?:at|of)|for\s+the\s+(?:year|period)\s+ended?)\s+"
        r"(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}|\d{4}[/-]\d{2}[/-]\d{2}|"
        r"december\s+31,?\s+\d{4}|31\s+december\s+\d{4}|31\s+march\s+\d{4})",
        text, re.IGNORECASE)
    report_date = date_m.group(1).title() if date_m else "N/A"

    # ── Income Statement ────────────────────────────────────────────────────────
    profit_curr, profit_prev = find_two_values(text, [
        r"profit\s+after\s+tax(?:ation)?",
        r"(?:net\s+)?(?:profit|income|loss)\s+(?:for\s+the\s+year|after\s+tax)",
        r"loss\s+for\s+the\s+year",
    ])

    op_income_curr, op_income_prev = find_two_values(text, [
        r"total\s+operating\s+income",
        r"operating\s+income",
        r"(?:net\s+)?income\s+before\s+provisions",
    ])

    int_income_curr, int_income_prev = find_two_values(text, [
        r"interest\s+income(?:\s+calculated)?",
        r"total\s+interest\s+income",
    ])

    # ── Balance Sheet ───────────────────────────────────────────────────────────
    total_assets_curr, total_assets_prev = find_two_values(text, [
        r"total\s+assets",
    ])

    total_liab_curr, total_liab_prev = find_two_values(text, [
        r"total\s+liabilities",
    ])

    loans_curr, loans_prev = find_two_values(text, [
        r"loans\s+and\s+(?:receivables|advances)[^,
]{0,30}net",
        r"loans\s+and\s+(?:receivables|advances\s+to\s+customers)",
        r"total\s+loans\s+and\s+advances",
    ])

    deposits_curr, deposits_prev = find_two_values(text, [
        r"deposits\s+from\s+customers",
        r"total\s+(?:customer\s+)?deposits",
    ])

    provisions_curr, provisions_prev = find_two_values(text, [
        r"(?:^|\s)provisions?",
        r"total\s+provisions?",
        r"specific\s+provisions?",
    ])

    # ── Liquidity ───────────────────────────────────────────────────────────────
    # LMR / plain liquidity ratio
    lmr_curr, lmr_prev = None, None
    lmr_patterns = [
        r"average\s+liquidity\s+maintenance\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        r"average\s+liquidity\s+(?:maintenance\s+)?ratio[^\d]{0,60}([\d.]+)\s*%",
        r"liquidity\s+maintenance\s+ratio[^\d]{0,80}([\d.]+)\s*%[^\d]{0,80}([\d.]+)\s*%",
    ]
    for pat in lmr_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            lmr_curr = float(m.group(1))
            lmr_prev = float(m.group(2)) if m.lastindex >= 2 else None
            break
    if lmr_curr is None:
        # plain "average liquidity ratio"
        m = re.search(
            r"average\s+liquidity\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
            text, re.IGNORECASE)
        if m:
            lmr_curr = float(m.group(1))
            lmr_prev = float(m.group(2))
        else:
            m2 = re.search(r"average\s+liquidity\s+ratio[^\d]{0,60}([\d.]+)\s*%", text, re.IGNORECASE)
            if m2:
                lmr_curr = float(m2.group(1))

    # CFR
    cfr_curr, cfr_prev = None, None
    m = re.search(
        r"average\s+core\s+funding\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        text, re.IGNORECASE)
    if m:
        cfr_curr = float(m.group(1))
        cfr_prev = float(m.group(2))
    else:
        m2 = re.search(r"average\s+core\s+funding\s+ratio[^\d]{0,60}([\d.]+)\s*%", text, re.IGNORECASE)
        if m2:
            cfr_curr = float(m2.group(1))

    # Leverage ratio
    lev_curr, lev_prev = None, None
    m = re.search(r"leverage\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
                  text, re.IGNORECASE)
    if m:
        lev_curr = float(m.group(1))
        lev_prev = float(m.group(2))

    # Capital ratios
    cet1_curr, cet1_prev = None, None
    m = re.search(
        r"(?:common\s+equity\s+tier\s+1|CET[- ]?1)[^\d]{0,80}([\d.]+)\s*%[^\d]{0,80}([\d.]+)\s*%",
        text, re.IGNORECASE)
    if m:
        cet1_curr = float(m.group(1))
        cet1_prev = float(m.group(2))

    # ── Business description ────────────────────────────────────────────────────
    desc = ""
    for pat in [r"business\s+activities?\s*
(.*?)

",
                r"principal\s+activities?\s*
(.*?)

",
                r"the\s+(?:branch|company)\s+provides?\s+(.{80,400}?)\.",
                r"the\s+(?:branch|company)\s+primarily\s+(.{60,300}?)\."]:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(raw) > 40:
                desc = raw[:400]
                break

    return {
        "entity": entity,
        "report_date": report_date,
        "currency": currency,
        "unit_mult": unit_mult,
        "unit_label": unit_label,
        "profit_curr": profit_curr,
        "profit_prev": profit_prev,
        "op_income_curr": op_income_curr,
        "op_income_prev": op_income_prev,
        "int_income_curr": int_income_curr,
        "int_income_prev": int_income_prev,
        "total_assets_curr": total_assets_curr,
        "total_assets_prev": total_assets_prev,
        "total_liab_curr": total_liab_curr,
        "total_liab_prev": total_liab_prev,
        "loans_curr": loans_curr,
        "loans_prev": loans_prev,
        "deposits_curr": deposits_curr,
        "deposits_prev": deposits_prev,
        "provisions_curr": provisions_curr,
        "provisions_prev": provisions_prev,
        "lmr_curr": lmr_curr,
        "lmr_prev": lmr_prev,
        "cfr_curr": cfr_curr,
        "cfr_prev": cfr_prev,
        "lev_curr": lev_curr,
        "lev_prev": lev_prev,
        "cet1_curr": cet1_curr,
        "cet1_prev": cet1_prev,
        "description": desc,
    }


def render_kpi(label, curr, prev, unit_mult, currency, is_pct=False, invert=False):
    if is_pct:
        val_str = f"{curr:.1f}%" if curr is not None else "N/A"
        c_str, cls = chg(curr, prev, pct=True)
    else:
        val_str = f"{currency} {fmt(curr, unit_mult)}" if curr is not None else "N/A"
        c_str, cls = chg(curr, prev)
    if invert:
        cls = "dn" if cls == "up" else ("up" if cls == "dn" else "nt")
    b = badge(c_str, cls) if c_str != "N/A" else ""
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{label}</div>
        <div class="card-value">{val_str}{b}</div>
        <div class="card-sub">vs prior period</div>
    </div>""", unsafe_allow_html=True)


def render_table_row(label, curr, prev, unit_mult, currency, is_pct=False, bold=False):
    if is_pct:
        cv = f"{curr:.1f}%" if curr is not None else "—"
        pv = f"{prev:.1f}%" if prev is not None else "—"
        c_str, cls = chg(curr, prev, pct=True)
    else:
        cv = f"{currency} {fmt(curr, unit_mult)}" if curr is not None else "—"
        pv = f"{currency} {fmt(prev, unit_mult)}" if prev is not None else "—"
        c_str, cls = chg(curr, prev)
    b = badge(c_str, cls) if c_str != "N/A" else ""
    row_cls = "bold-row" if bold else ""
    return f"""<tr class="{row_cls}">
        <td>{label}</td>
        <td class="num">{cv}</td>
        <td class="num">{pv}</td>
        <td class="num">{b}</td>
    </tr>"""


def render_report(d):
    um = d["unit_mult"]
    cy = d["currency"]

    # Entity header
    st.markdown(f"""
    <div class="entity-header">
        <h2>{d['entity']}</h2>
        <div class="meta">Reporting period ending {d['report_date']} &nbsp;·&nbsp;
        Figures in {cy} {d['unit_label']}</div>
    </div>""", unsafe_allow_html=True)

    # Business description
    if d["description"]:
        st.markdown(f'<div class="info-box">📋 <strong>Business:</strong> {d["description"]}</div>',
                    unsafe_allow_html=True)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi("Total Assets", d["total_assets_curr"], d["total_assets_prev"], um, cy)
    with c2: render_kpi("Net Profit / (Loss)", d["profit_curr"], d["profit_prev"], um, cy)
    with c3: render_kpi("Avg LMR", d["lmr_curr"], d["lmr_prev"], 1, "", is_pct=True)
    with c4: render_kpi("Avg CFR", d["cfr_curr"], d["cfr_prev"], 1, "", is_pct=True)

    # Income & balance sheet table
    st.markdown('<div class="section-header">📊 Financial Summary</div>', unsafe_allow_html=True)

    rows_inc = ""
    rows_inc += render_table_row("Interest Income", d["int_income_curr"], d["int_income_prev"], um, cy)
    rows_inc += render_table_row("Total Operating Income", d["op_income_curr"], d["op_income_prev"], um, cy)
    rows_inc += render_table_row("Profit / (Loss) after Tax", d["profit_curr"], d["profit_prev"], um, cy, bold=True)
    rows_inc += render_table_row("Total Assets", d["total_assets_curr"], d["total_assets_prev"], um, cy, bold=True)
    rows_inc += render_table_row("Total Liabilities", d["total_liab_curr"], d["total_liab_prev"], um, cy)
    rows_inc += render_table_row("Loans & Receivables", d["loans_curr"], d["loans_prev"], um, cy)
    rows_inc += render_table_row("Customer Deposits", d["deposits_curr"], d["deposits_prev"], um, cy)
    rows_inc += render_table_row("Provisions", d["provisions_curr"], d["provisions_prev"], um, cy)

    st.markdown(f"""
    <table class="styled">
      <thead><tr>
        <th style="width:40%">Line Item</th>
        <th class="num" style="width:20%">Current</th>
        <th class="num" style="width:20%">Prior</th>
        <th class="num" style="width:20%">Change</th>
      </tr></thead>
      <tbody>{rows_inc}</tbody>
    </table>""", unsafe_allow_html=True)

    # Ratios table
    st.markdown('<div class="section-header">📈 Regulatory & Capital Ratios</div>', unsafe_allow_html=True)

    rows_rat = ""
    rows_rat += render_table_row("Avg Liquidity Maint. Ratio (LMR)", d["lmr_curr"], d["lmr_prev"], 1, "", is_pct=True)
    rows_rat += render_table_row("Avg Core Funding Ratio (CFR)", d["cfr_curr"], d["cfr_prev"], 1, "", is_pct=True)
    rows_rat += render_table_row("CET1 Capital Ratio", d["cet1_curr"], d["cet1_prev"], 1, "", is_pct=True)
    rows_rat += render_table_row("Leverage Ratio", d["lev_curr"], d["lev_prev"], 1, "", is_pct=True)

    st.markdown(f"""
    <table class="styled">
      <thead><tr>
        <th style="width:40%">Ratio</th>
        <th class="num" style="width:20%">Current Period</th>
        <th class="num" style="width:20%">Prior Period</th>
        <th class="num" style="width:20%">Change (pp)</th>
      </tr></thead>
      <tbody>{rows_rat}</tbody>
    </table>""", unsafe_allow_html=True)

    # CSV export
    rows = [
        ["Entity", d["entity"]],
        ["Report Date", d["report_date"]],
        ["Currency", d["currency"]],
        ["Unit Label", d["unit_label"]],
        ["Interest Income (curr)", d["int_income_curr"]],
        ["Interest Income (prev)", d["int_income_prev"]],
        ["Total Operating Income (curr)", d["op_income_curr"]],
        ["Total Operating Income (prev)", d["op_income_prev"]],
        ["Profit/Loss after Tax (curr)", d["profit_curr"]],
        ["Profit/Loss after Tax (prev)", d["profit_prev"]],
        ["Total Assets (curr)", d["total_assets_curr"]],
        ["Total Assets (prev)", d["total_assets_prev"]],
        ["Total Liabilities (curr)", d["total_liab_curr"]],
        ["Total Liabilities (prev)", d["total_liab_prev"]],
        ["Loans & Receivables (curr)", d["loans_curr"]],
        ["Loans & Receivables (prev)", d["loans_prev"]],
        ["Customer Deposits (curr)", d["deposits_curr"]],
        ["Customer Deposits (prev)", d["deposits_prev"]],
        ["Provisions (curr)", d["provisions_curr"]],
        ["Provisions (prev)", d["provisions_prev"]],
        ["Avg LMR % (curr)", d["lmr_curr"]],
        ["Avg LMR % (prev)", d["lmr_prev"]],
        ["Avg CFR % (curr)", d["cfr_curr"]],
        ["Avg CFR % (prev)", d["cfr_prev"]],
        ["CET1 % (curr)", d["cet1_curr"]],
        ["CET1 % (prev)", d["cet1_prev"]],
        ["Leverage Ratio % (curr)", d["lev_curr"]],
        ["Leverage Ratio % (prev)", d["lev_prev"]],
    ]
    df = pd.DataFrame(rows, columns=["Field", "Value"])
    csv = df.to_csv(index=False)
    st.markdown("---")
    st.download_button("⬇️  Download CSV", csv,
                       file_name=f"{d['entity'].replace(' ','_')}_extracted.csv",
                       mime="text/csv")


# ─── FILE UPLOADER ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#fefce8; border:1px solid #fde68a; border-radius:10px;
            padding:14px 18px; margin-bottom:18px; font-size:0.875rem; color:#78350f;">
    <strong>⚠️ File Requirement:</strong> Your PDF must contain <strong>selectable/copyable text</strong>
    (i.e. a digital PDF, not a scanned image). To check: open the PDF, try to highlight a word with
    your cursor — if you can select text, it will work. Scanned PDFs (where text appears as an image)
    are <strong>not supported</strong> and will return N/A for most fields.
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Drop an HKMA Banking Disclosure PDF here (text-based PDFs only)",
    type=["pdf"],
    help="Must be a digital/text-based PDF — not a scanned document"
)

if uploaded:
    with st.spinner("Reading PDF…"):
        text = extract_text(uploaded)
    with st.spinner("Extracting data…"):
        data = extract_all(text)

    # Show any missing-field warning
    missing = [k for k in ["total_assets_curr", "profit_curr"] if data[k] is None]
    if missing:
        st.markdown(
            f'<div class="warn-box">⚠️ Could not extract: {", ".join(missing)}. '
            f'This PDF may use a non-standard layout. Values will show as N/A.</div>',
            unsafe_allow_html=True)

    render_report(data)

else:
    st.markdown("""
    <div class="card" style="text-align:center; padding: 48px; border: 2px dashed #d1d5db;">
        <div style="font-size:3rem; margin-bottom:12px;">📄</div>
        <div style="font-size:1.1rem; font-weight:600; color:#374151; margin-bottom:8px;">
            Upload an HKMA Disclosure PDF to get started</div>
        <div style="color:#9ca3af; font-size:0.875rem;">
            Supports: Natixis · UBS · JPMorgan · ORIX · Standard Chartered · HSBC · and more
        </div>
    </div>""", unsafe_allow_html=True)
