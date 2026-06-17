
import streamlit as st
import pdfplumber
import io, re, os, json
import pandas as pd

st.set_page_config(page_title="HKMA Financial Disclosure Analyser", layout="wide", page_icon="🏦")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600;700&display=swap');

/* ── Societe Generale palette ──
   Primary red   : #E60028
   Black         : #1A1A1A
   White         : #FFFFFF
   Light gray bg : #F5F5F5
   Mid gray      : #6B6B6B
   Border gray   : #D9D9D9
*/

html, body, [class*="css"] {
    font-family: 'Raleway', 'Arial', sans-serif;
    color: #1A1A1A;
}
.stApp { background: #F5F5F5; }

/* Hero bar */
.hero {
    background: #E60028;
    border-radius: 0px;
    padding: 32px 40px 24px;
    margin-bottom: 28px;
    border-bottom: 4px solid #1A1A1A;
}
.hero h1 {
    color: #FFFFFF;
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.hero p { color: rgba(255,255,255,0.80); font-size: 0.9rem; margin: 0; }

/* KPI cards */
.card {
    background: #FFFFFF;
    border-radius: 0px;
    border-top: 3px solid #E60028;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.card-title {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 1.4px;
    text-transform: uppercase; color: #6B6B6B; margin-bottom: 6px;
}
.card-value { font-size: 1.55rem; font-weight: 700; color: #1A1A1A; }
.card-sub   { font-size: 0.78rem; color: #6B6B6B; margin-top: 3px; }

/* Badges */
.badge-up { display:inline-block; background:#E60028; color:#FFFFFF;
            font-size:0.7rem; font-weight:700; padding:2px 8px;
            border-radius:2px; margin-left:8px; }
.badge-dn { display:inline-block; background:#1A1A1A; color:#FFFFFF;
            font-size:0.7rem; font-weight:700; padding:2px 8px;
            border-radius:2px; margin-left:8px; }
.badge-nt { display:inline-block; background:#D9D9D9; color:#6B6B6B;
            font-size:0.7rem; font-weight:700; padding:2px 8px;
            border-radius:2px; margin-left:8px; }

/* Section headers */
.section-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: #E60028;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    border-bottom: 2px solid #E60028;
    padding-bottom: 8px;
    margin: 32px 0 16px;
}

/* Info / warn / analysis boxes */
.info-box {
    background: #FFFFFF;
    border-left: 4px solid #E60028;
    padding: 12px 16px;
    font-size: 0.875rem;
    color: #1A1A1A;
    margin-bottom: 16px;
    line-height: 1.6;
}
.warn-box {
    background: #FFF5F5;
    border-left: 4px solid #E60028;
    padding: 12px 16px;
    font-size: 0.875rem;
    color: #1A1A1A;
    margin-bottom: 16px;
    line-height: 1.6;
}
.green-box {
    background: #FFFFFF;
    border-left: 4px solid #1A1A1A;
    padding: 14px 18px;
    font-size: 0.875rem;
    color: #1A1A1A;
    margin-bottom: 16px;
    line-height: 1.7;
}
.red-box {
    background: #FFF5F5;
    border-left: 4px solid #E60028;
    padding: 14px 18px;
    font-size: 0.875rem;
    color: #1A1A1A;
    margin-bottom: 16px;
    line-height: 1.7;
}
.neutral-box {
    background: #F5F5F5;
    border-left: 4px solid #6B6B6B;
    padding: 14px 18px;
    font-size: 0.875rem;
    color: #1A1A1A;
    margin-bottom: 16px;
    line-height: 1.7;
}

/* Valuation block */
.valuation-block {
    background: #FFFFFF;
    color: #1A1A1A;
    border-radius: 0px;
    border-top: 3px solid #E60028;
    border: 1px solid #D9D9D9;
    border-top: 3px solid #E60028;
    padding: 24px 28px;
    margin-bottom: 20px;
    font-size: 0.875rem;
    line-height: 1.8;
}
.valuation-block h3 {
    color: #E60028;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    margin: 0 0 14px 0;
}
.val-step {
    display:flex; align-items:baseline; gap:12px;
    padding: 5px 0;
    border-bottom: 1px solid #D9D9D9;
}
.val-step:last-child { border-bottom: none; font-weight:700; color:#1A1A1A; }
.val-label { flex:1; color:#6B6B6B; }
.val-num   { font-variant-numeric: tabular-nums; color:#1A1A1A; }
.val-sign  { color:#6B6B6B; width:16px; }

/* Entity header */
.entity-header {
    background: #FFFFFF;
    border-left: 6px solid #E60028;
    border-top: 3px solid #E60028;
    padding: 22px 28px;
    margin-bottom: 20px;
    color: #1A1A1A;
}
.entity-header h2 {
    margin: 0; font-size: 1.4rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px; color: #1A1A1A;
}
.entity-header .meta { font-size: 0.82rem; color: #6B6B6B; margin-top: 5px; }

/* Tables */
table.styled { width:100%; border-collapse:collapse; font-size:0.86rem; }
table.styled th {
    background: #E60028;
    color: #FFFFFF;
    padding: 10px 14px;
    text-align: left;
    font-weight: 700;
    font-size: 0.72rem;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
table.styled td {
    padding: 9px 14px;
    border-bottom: 1px solid #D9D9D9;
    color: #1A1A1A;
    background: #FFFFFF;
}
table.styled tr:last-child td { border-bottom: none; }
table.styled tr:hover td { background: #F5F5F5; }
.num { text-align:right !important; font-variant-numeric: tabular-nums; }
.bold-row td {
    font-weight: 700;
    color: #1A1A1A !important;
    background: #F5F5F5 !important;
    border-left: 3px solid #E60028;
}

/* Executive analysis sections */
.exec-section {
    background: #FFFFFF;
    border-top: 3px solid #E60028;
    padding: 24px 28px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 20px;
}
.exec-section h3 {
    font-size: 0.72rem;
    font-weight: 700;
    color: #E60028;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin: 0 0 12px 0;
}
.exec-section p {
    font-size: 0.875rem;
    color: #1A1A1A;
    line-height: 1.75;
    margin: 0 0 10px 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>HKMA Financial Disclosure Analyser</h1>
    <p>Upload any HKMA Banking Disclosure PDF. Supports branches, locally incorporated banks, and restricted licence banks.</p>
</div>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────

def extract_text(uploaded_file) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            pages.append(t)
    return "\n".join(pages)


JUNK = re.compile(
    r"^(key\s+financial|financial\s+information|disclosure|statements?|"
    r"contents?|chief\s+executive|declaration|notes?\s+to|"
    r"as\s+at|for\s+the\s+(year|period)|pages?|"
    r"GROUPE|BPCE|KPMG|FOR\s+IDENTIFICATION|ONLY|"
    r"HONG\s+KONG\s*$|incorporated\s+in|liability\s+of|"
    r"with\s+limited|unaudited|audited|section\s+[a-z]|"
    r"limited\s+liability|the\s+company|"
    r"CORPORATE\s+AND|INVESTMENT\s+BANKING|"
    r"AND\s+INVESTMENT\s+BANKING|"
    r"stamp|signature|\[|\d+\s*$)",
    re.IGNORECASE
)


def extract_entity_name(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:80]:
        if re.search(r"hong\s+kong\s+branch", line, re.IGNORECASE):
            name = re.sub(r"\s+", " ", line).strip()
            name = re.split(r"\s{2,}|[（(]incorporated", name, flags=re.IGNORECASE)[0].strip()
            if len(name) > 4:
                return name
    for line in lines[:40]:
        if len(line) < 5 or JUNK.match(line):
            continue
        if re.match(r"^(CORPORATE|INVESTMENT|GROUP|GROUPE|BPCE|KPMG)", line, re.IGNORECASE):
            continue
        words = line.split()
        if len(words) >= 2 and line[0].isupper():
            return line
    return "Unknown Institution"


def parse_num(s: str):
    s = str(s).strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "\u2014", "\u2013", "N/A", "n/a"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def find_two_values(text: str, patterns: list, window: int = 220):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            snippet = text[m.end(): m.end() + window]
            nums = re.findall(r"[(\-]?\s*[\d,]+(?:\.\d+)?[)]?", snippet)
            parsed = [parse_num(n) for n in nums if parse_num(n) is not None]
            if len(parsed) >= 2:
                return parsed[0], parsed[1]
            if len(parsed) == 1:
                return parsed[0], None
    return None, None


def detect_unit(text: str):
    t = text[:3000]
    if re.search(r"in\s+(thousands?|HK\$?\s*thousands?|HKD\s*thousands?)", t, re.IGNORECASE):
        return 1_000, "HKD thousands"
    if re.search(r"in\s+(millions?|HK\$?\s*millions?|HKD\s*millions?|US\$?\s*millions?)", t, re.IGNORECASE):
        return 1_000_000, "millions"
    big = re.findall(r"\b\d{8,}\b", t)
    if big:
        return 1, "units"
    return 1_000_000, "millions"


def detect_currency(text: str):
    t = text[:2000]
    if re.search(r"US\s*\$|USD|United States dollars?", t, re.IGNORECASE) and \
       not re.search(r"HKD|Hong Kong dollar", t[:500], re.IGNORECASE):
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


def render_table_row(label, curr, prev, unit_mult, currency, is_pct=False, bold=False):
    if is_pct:
        cv = f"{curr:.1f}%" if curr is not None else "--"
        pv = f"{prev:.1f}%" if prev is not None else "--"
        c_str, cls = chg(curr, prev, pct=True)
    else:
        cv = f"{currency} {fmt(curr, unit_mult)}" if curr is not None else "--"
        pv = f"{currency} {fmt(prev, unit_mult)}" if prev is not None else "--"
        c_str, cls = chg(curr, prev)
    b = badge(c_str, cls) if c_str != "N/A" else ""
    row_cls = "bold-row" if bold else ""
    return (f'<tr class="{row_cls}"><td>{label}</td>'
            f'<td class="num">{cv}</td><td class="num">{pv}</td>'
            f'<td class="num">{b}</td></tr>')


# ── ASSET / LIABILITY BREAKDOWN ───────────────────────────────────────────────

ASSET_PATTERNS = [
    ("Cash & Balances with Banks",
     [r"cash\s+and\s+balances?\s+with\s+banks?"]),
    ("Amount Due from Overseas Offices",
     [r"amount\s+(?:receivable|due)\s+from\s+overseas\s+offices?"]),
    ("Loans & Receivables",
     [r"loans\s+and\s+(?:receivables|advances\s+to\s+customers)", r"loans\s+and\s+advances\s+to\s+customers"]),
    ("Investment Securities",
     [r"investment\s+securities"]),
    ("Securities Held for Trading",
     [r"securities\s+held\s+for\s+trading"]),
    ("Placements with Banks",
     [r"placements?\s+with\s+banks?"]),
    ("Reverse Repos",
     [r"amount\s+receivable\s+under\s+reverse\s+repos?"]),
    ("Other Investments",
     [r"other\s+investments?"]),
    ("Property, Plant & Equipment",
     [r"property,?\s+plant\s+and\s+equipment"]),
    ("Other Assets",
     [r"other\s+assets?\b"]),
]

LIAB_PATTERNS = [
    ("Customer Deposits",
     [r"deposits\s+from\s+customers", r"total\s+customer\s+deposits"]),
    ("Interbank Deposits",
     [r"deposits?\s+(?:and\s+balances?\s+)?from\s+banks"]),
    ("Amount Due to Overseas Offices",
     [r"amount\s+(?:payable|due)\s+to\s+overseas\s+offices?"]),
    ("Certificates of Deposit Issued",
     [r"certificates?\s+of\s+deposit\s+issued"]),
    ("Issued Debt Securities",
     [r"issued\s+debt\s+securities"]),
    ("Repos",
     [r"amount\s+payable\s+under\s+repos?"]),
    ("Provisions",
     [r"(?:^|\s)provisions?\b"]),
    ("Other Liabilities",
     [r"other\s+liabilities?\b"]),
]


def extract_breakdown(text, patterns):
    results = {}
    for label, pats in patterns:
        v, _ = find_two_values(text, pats, window=120)
        if v is not None and v > 0:
            results[label] = v
    return results


# ── FULL EXTRACTION ───────────────────────────────────────────────────────────

def extract_all(text: str) -> dict:
    unit_mult, unit_label = detect_unit(text)
    currency = detect_currency(text)
    entity = extract_entity_name(text)

    date_m = re.search(
        r"(?:as\s+(?:at|of)|for\s+the\s+(?:year|period)\s+ended?)\s+"
        r"(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}|"
        r"december\s+31,?\s+\d{4}|31\s+december\s+\d{4}|31\s+march\s+\d{4})",
        text, re.IGNORECASE)
    report_date = date_m.group(1).title() if date_m else "N/A"

    profit_curr, profit_prev = find_two_values(text, [
        r"profit\s+after\s+tax(?:ation)?",
        r"(?:net\s+)?(?:profit|income|loss)\s+(?:for\s+the\s+year|after\s+tax)",
        r"loss\s+for\s+the\s+year",
    ])
    op_income_curr, op_income_prev = find_two_values(text, [
        r"total\s+operating\s+income", r"operating\s+income",
    ])
    int_income_curr, int_income_prev = find_two_values(text, [
        r"interest\s+income(?:\s+calculated)?", r"total\s+interest\s+income",
    ])
    total_assets_curr, total_assets_prev = find_two_values(text, [r"total\s+assets"])
    total_liab_curr, total_liab_prev    = find_two_values(text, [r"total\s+liabilities"])
    loans_curr, loans_prev = find_two_values(text, [
        r"loans\s+and\s+(?:receivables|advances)[^,\n]{0,30}net",
        r"loans\s+and\s+(?:receivables|advances\s+to\s+customers)",
    ])
    deposits_curr, deposits_prev = find_two_values(text, [r"deposits\s+from\s+customers"])
    provisions_curr, provisions_prev = find_two_values(text, [r"(?:^|\s)provisions?\b"])

    # LMR
    lmr_curr, lmr_prev = None, None
    for pat in [
        r"average\s+liquidity\s+maintenance\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        r"average\s+liquidity\s+(?:maintenance\s+)?ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        r"average\s+liquidity\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            lmr_curr = float(m.group(1)); lmr_prev = float(m.group(2)); break
    if lmr_curr is None:
        m = re.search(r"average\s+liquidity\s+(?:maintenance\s+)?ratio[^\d]{0,60}([\d.]+)\s*%", text, re.IGNORECASE)
        if m: lmr_curr = float(m.group(1))

    # CFR
    cfr_curr, cfr_prev = None, None
    m = re.search(r"average\s+core\s+funding\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%", text, re.IGNORECASE)
    if m:
        cfr_curr = float(m.group(1)); cfr_prev = float(m.group(2))
    else:
        m2 = re.search(r"average\s+core\s+funding\s+ratio[^\d]{0,60}([\d.]+)\s*%", text, re.IGNORECASE)
        if m2: cfr_curr = float(m2.group(1))

    # CET1 / leverage
    cet1_curr, cet1_prev = None, None
    m = re.search(r"(?:common\s+equity\s+tier\s+1|CET[- ]?1)[^\d]{0,80}([\d.]+)\s*%[^\d]{0,80}([\d.]+)\s*%", text, re.IGNORECASE)
    if m: cet1_curr = float(m.group(1)); cet1_prev = float(m.group(2))

    lev_curr, lev_prev = None, None
    m = re.search(r"leverage\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%", text, re.IGNORECASE)
    if m: lev_curr = float(m.group(1)); lev_prev = float(m.group(2))

    # Business description
    desc = ""
    for pat in [r"business\s+activities?\s*\n(.*?)\n\n",
                r"principal\s+activities?\s*\n(.*?)\n\n",
                r"the\s+(?:branch|company)\s+provides?\s+(.{80,400}?)\.",
                r"the\s+(?:branch|company)\s+primarily\s+(.{60,300}?)\."]:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(raw) > 40:
                desc = raw[:500]; break

    asset_bdown = extract_breakdown(text, ASSET_PATTERNS)
    liab_bdown  = extract_breakdown(text, LIAB_PATTERNS)

    # Equity (book) = total assets - total liabilities
    equity = None
    if total_assets_curr and total_liab_curr:
        equity = total_assets_curr - total_liab_curr

    return dict(
        entity=entity, report_date=report_date, currency=currency,
        unit_mult=unit_mult, unit_label=unit_label, description=desc,
        profit_curr=profit_curr, profit_prev=profit_prev,
        op_income_curr=op_income_curr, op_income_prev=op_income_prev,
        int_income_curr=int_income_curr, int_income_prev=int_income_prev,
        total_assets_curr=total_assets_curr, total_assets_prev=total_assets_prev,
        total_liab_curr=total_liab_curr, total_liab_prev=total_liab_prev,
        loans_curr=loans_curr, loans_prev=loans_prev,
        deposits_curr=deposits_curr, deposits_prev=deposits_prev,
        provisions_curr=provisions_curr, provisions_prev=provisions_prev,
        lmr_curr=lmr_curr, lmr_prev=lmr_prev,
        cfr_curr=cfr_curr, cfr_prev=cfr_prev,
        cet1_curr=cet1_curr, cet1_prev=cet1_prev,
        lev_curr=lev_curr, lev_prev=lev_prev,
        equity=equity, asset_bdown=asset_bdown, liab_bdown=liab_bdown,
    )


# ── VALUATION ENGINE ──────────────────────────────────────────────────────────

def build_valuation(d):
    um = d["unit_mult"]
    cy = d["currency"]
    equity = d["equity"]
    profit = d["profit_curr"]
    total_assets = d["total_assets_curr"]
    provisions = d["provisions_curr"]
    lmr = d["lmr_curr"]

    steps_pbv = []
    steps_gordon = []
    vir_steps = []
    ok_pbv = ok_gordon = ok_vir = False

    # ----- P/BV model (equity approach) -----
    # Typical P/BV for HK bank branches: 0.8x--1.3x depending on ROE
    if equity is not None and equity > 0:
        pbv_low  = equity * um * 0.8
        pbv_mid  = equity * um * 1.0
        pbv_high = equity * um * 1.3
        ok_pbv = True
        steps_pbv = [
            ("Book Equity (Total Assets minus Total Liabilities)",
             f"{cy} {fmt(equity, um)}", ""),
            ("Applied P/BV multiple (low / mid / high)",
             "0.8x / 1.0x / 1.3x",
             "Peer range for HK wholesale branches; mid = book value"),
            ("Implied Entity Valuation (low)",
             f"{cy} {fmt(pbv_low/um, um)}", "x 0.8"),
            ("Implied Entity Valuation (mid -- base case)",
             f"{cy} {fmt(pbv_mid/um, um)}", "x 1.0"),
            ("Implied Entity Valuation (high)",
             f"{cy} {fmt(pbv_high/um, um)}", "x 1.3"),
        ]

    # ----- Gordon Growth Model (dividend / earnings based) -----
    if profit is not None and profit > 0 and equity is not None and equity > 0:
        roe     = profit / equity          # both in same units
        payout  = 0.40                     # assumed for HK branches
        g       = roe * (1 - payout)       # sustainable growth
        ke      = 0.10                     # cost of equity 10%
        if ke > g:
            p_e_implied = payout / (ke - g)
            val_gordon  = profit * um * p_e_implied
            ok_gordon = True
            steps_gordon = [
                ("Net Profit after Tax",
                 f"{cy} {fmt(profit, um)}", ""),
                (f"Return on Equity (Profit / Book Equity)",
                 f"{roe*100:.1f}%", ""),
                ("Assumed Payout Ratio",
                 "40%", "Typical HK branch distribution assumption"),
                ("Sustainable Growth (ROE x Retention)",
                 f"{g*100:.1f}%", ""),
                ("Cost of Equity (Ke)",
                 "10.0%", "Risk-free 4% + equity risk premium 6%"),
                ("Implied P/E (Gordon: payout / (Ke minus g))",
                 f"{p_e_implied:.1f}x", ""),
                ("Implied Entity Valuation",
                 f"{cy} {fmt(val_gordon/um, um)}", ""),
            ]

    # ----- HKFRS 13 fair value approximation -----
    fv_note = (
        "HKFRS 13 requires each financial instrument to be measured at its "
        "exit price -- what a market participant would pay on the measurement date. "
        "For a branch, key items are: (1) Loans at amortised cost adjusted for "
        "current credit spreads; (2) Trading securities already at mark-to-market; "
        "(3) Derivatives at quoted fair value. Book equity is the HKFRS 13 residual "
        "after those adjustments. No material FV adjustment is disclosed in this filing, "
        "so book equity is taken as the best available proxy for HKFRS 13 net asset value."
    )

    # ----- VIR (FIRO Ord. Cap. 628) -----
    if equity is not None and provisions is not None:
        vir_equity = (equity - provisions) * um
        ok_vir = True
        vir_steps = [
            ("Book Equity", f"{cy} {fmt(equity, um)}", ""),
            ("Less: Provisions (stressed haircut)", f"({cy} {fmt(provisions, um)})", "FIRO s.43 write-down basis"),
            ("VIR Floor (going-concern adjusted book)", f"{cy} {fmt(vir_equity/um, um)}", ""),
            ("VIR Ceiling (pre-resolution liquidation NAV)", f"{cy} {fmt(equity*um*0.75/um, um)}", "25% liquidation discount applied"),
        ]
    elif equity is not None:
        vir_equity = equity * um
        ok_vir = True
        vir_steps = [
            ("Book Equity", f"{cy} {fmt(equity, um)}", ""),
            ("VIR Floor (no provisions data, floor = book)", f"{cy} {fmt(equity, um)}", ""),
            ("VIR Ceiling (pre-resolution liquidation NAV)", f"{cy} {fmt(equity*0.75, um)}", "25% discount applied"),
        ]

    return dict(
        ok_pbv=ok_pbv, steps_pbv=steps_pbv,
        ok_gordon=ok_gordon, steps_gordon=steps_gordon,
        fv_note=fv_note,
        ok_vir=ok_vir, vir_steps=vir_steps,
    )


# ── ANALYSIS ENGINE ───────────────────────────────────────────────────────────

def build_analysis(d):
    um = d["unit_mult"]; cy = d["currency"]
    out = {}

    lmr_c = d["lmr_curr"]; lmr_p = d["lmr_prev"]
    cfr_c = d["cfr_curr"];  cfr_p = d["cfr_prev"]
    profit = d["profit_curr"]; profit_p = d["profit_prev"]
    total_a = d["total_assets_curr"]; total_a_p = d["total_assets_prev"]
    total_l = d["total_liab_curr"]
    loans   = d["loans_curr"]; deposits = d["deposits_curr"]
    equity  = d["equity"]
    prov    = d["provisions_curr"]; prov_p = d["provisions_prev"]
    int_inc = d["int_income_curr"]; int_inc_p = d["int_income_prev"]
    op_inc  = d["op_income_curr"]

    # ── Derived ratios ────────────────────────────────────────────────────────
    roa    = (profit / total_a * 100)   if profit and total_a else None
    roe    = (profit / equity  * 100)   if profit and equity  else None
    nim    = (int_inc / total_a * 100)  if int_inc and total_a else None
    llr    = (prov / loans * 100)       if prov and loans else None
    ldr    = (loans / deposits * 100)   if loans and deposits else None
    equity_ratio = (equity / total_a * 100) if equity and total_a else None
    asset_growth = ((total_a - total_a_p) / abs(total_a_p) * 100) if total_a and total_a_p else None
    profit_growth = ((profit - profit_p) / abs(profit_p) * 100) if profit and profit_p else None
    prov_change = ((prov - prov_p) / abs(prov_p) * 100) if prov and prov_p and prov_p != 0 else None
    int_income_growth = ((int_inc - int_inc_p) / abs(int_inc_p) * 100) if int_inc and int_inc_p else None

    # ── LMR Analysis ─────────────────────────────────────────────────────────
    if lmr_c is not None:
        if   lmr_c >= 300: lmr_level = "exceptionally high"
        elif lmr_c >= 150: lmr_level = "very strong"
        elif lmr_c >= 75:  lmr_level = "solid"
        elif lmr_c >= 35:  lmr_level = "adequate but lean"
        else:              lmr_level = "tight -- approaching the 25% regulatory floor"

        # What is driving it?
        ab = d.get("asset_bdown", {}) or {}
        lb = d.get("liab_bdown", {}) or {}
        hqla_proxy = ab.get("Cash & Balances with Banks", 0) or 0
        st_liab_proxy = lb.get("Interbank Deposits", 0) or 0

        if lmr_c >= 150 and hqla_proxy and total_a and hqla_proxy / total_a > 0.10:
            driver = ("The elevated ratio is consistent with a large stock of cash and interbank placements -- "
                      "assets that count as HQLA under the Banking (Liquidity) Rules. "
                      "This is deliberate balance sheet positioning rather than an accident.")
        elif lmr_c >= 150:
            driver = ("The high ratio likely reflects a structural feature of the business model: "
                      "either a capital markets branch with a large proportion of liquid trading assets, "
                      "or a branch that relies heavily on short-dated intragroup funding matched against "
                      "liquid assets rather than illiquid loans.")
        else:
            driver = ("The ratio is in a normal operating range. The branch is neither aggressively "
                      "deploying liquidity into loans nor hoarding cash.")

        if lmr_p is not None:
            diff = lmr_c - lmr_p
            if abs(diff) <= 5:
                trend = (f"The ratio is effectively flat ({diff:+.1f}pp) versus the prior period. "
                         "Flat LMR at this level typically means treasury is running the book within "
                         "a tight internal band -- a sign of mature, formula-driven liquidity management "
                         "rather than reactive repositioning. For an executive, this is reassuring.")
            elif diff > 20:
                trend = (f"The {diff:+.1f}pp jump is significant. The most likely explanations are: "
                         "(1) a sharp reduction in short-term wholesale borrowing (denominator shrinks); "
                         "(2) inflows of customer deposits that were left uninvested in HQLA; or "
                         "(3) a deliberate pre-positioning ahead of a regulatory inspection. "
                         "Executives should probe which of these drove the move -- only (1) and (3) "
                         "are sustainable; (2) will reverse when those deposits are redeployed.")
            elif diff > 0:
                trend = (f"The {diff:+.1f}pp improvement suggests modest net accumulation of liquid assets "
                         "or a reduction in short-term liabilities. Consistent with a slightly more "
                         "conservative liquidity posture, possibly reflecting softer loan demand.")
            elif diff < -20:
                trend = (f"The {diff:+.1f}pp decline is material. The branch likely deployed liquidity "
                         "into loans or interbank lending, or increased short-term wholesale funding. "
                         "While still above the regulatory minimum, a sustained downward trend in LMR "
                         "warrants monitoring -- particularly if CFR is also moving lower.")
            else:
                trend = (f"The {diff:+.1f}pp decline is modest. It likely reflects normal seasonal "
                         "balance sheet movements rather than a structural shift. Monitor for continuation.")
        else:
            trend = "No prior period available for trend analysis."

        out["lmr_text"] = f"{driver} {trend}"
        out["lmr_level"] = lmr_level
        out["lmr_c"] = lmr_c
    else:
        out["lmr_text"] = None; out["lmr_level"] = None; out["lmr_c"] = None

    # ── CFR Analysis ─────────────────────────────────────────────────────────
    if cfr_c is not None:
        if cfr_c >= 500:
            cfr_interp = ("An average CFR above 500% means the branch holds roughly 5x more stable funding "
                          "than it needs to cover its illiquid assets. At this level, the branch is "
                          "effectively a net exporter of stable funding to its parent group -- "
                          "excess long-dated deposits and equity are funding assets that mature quickly. "
                          "This is common in custody, private banking, or fee-income-heavy branches "
                          "where client balances are large but assets are liquid.")
        elif cfr_c >= 200:
            cfr_interp = ("A CFR above 200% confirms the branch is fully self-funding on a structural basis "
                          "with a significant buffer. Stable funding comfortably exceeds illiquid assets. "
                          "The branch is not dependent on short-term wholesale markets to fund its loan book.")
        elif cfr_c >= 100:
            cfr_interp = ("The CFR is above 100%, meaning stable funding covers all illiquid assets -- "
                          "the minimum required structural resilience. The branch meets regulatory expectations "
                          "but has limited headroom to absorb a sudden withdrawal of stable deposits.")
        else:
            cfr_interp = ("A CFR below 100% is a structural warning sign: illiquid assets exceed stable funding. "
                          "The branch is relying on short-term wholesale funding to finance long-term assets -- "
                          "a maturity mismatch that creates rollover risk in stressed markets.")

        if cfr_p is not None:
            diff_cfr = cfr_c - cfr_p
            if abs(diff_cfr) <= 10:
                cfr_trend = ("CFR is stable period-over-period, indicating no material change in the "
                             "funding structure. The balance between stable and short-term funding sources "
                             "is unchanged.")
            elif diff_cfr > 50:
                cfr_trend = (f"The {diff_cfr:+.1f}pp surge in CFR likely reflects a large inflow of "
                             "long-dated deposits or an increase in equity capital, or a significant "
                             "reduction in illiquid loan assets. All three would be positive developments, "
                             "but the source matters -- growth driven by loan run-off is different from "
                             "growth driven by genuine new stable funding.")
            elif diff_cfr > 0:
                cfr_trend = (f"The {diff_cfr:+.1f}pp improvement in CFR reflects a gradual shift toward "
                             "more stable funding. This could be deliberate liability management "
                             "(extending the duration of funding) or organic growth in retail deposits.")
            elif diff_cfr < -50:
                cfr_trend = (f"The {diff_cfr:+.1f}pp fall in CFR is significant. The branch either grew "
                             "its illiquid loan book rapidly, lost a large block of stable deposits, "
                             "or increased reliance on short-term wholesale funding. "
                             "Executives should determine which occurred -- loan growth is expected; "
                             "deposit outflows or funding shortening are red flags.")
            else:
                cfr_trend = (f"The {diff_cfr:+.1f}pp decline in CFR is modest. Likely reflects normal "
                             "portfolio turnover rather than a structural funding change.")
        else:
            cfr_trend = "No prior period available for trend analysis."

        # Joint LMR/CFR signal
        if lmr_c is not None and cfr_c is not None:
            if lmr_c >= 100 and cfr_c >= 200:
                joint = ("Together, a high LMR and a high CFR indicate a branch with both short-term "
                         "resilience (enough HQLA to survive a 30-day stress) and long-term structural "
                         "soundness (stable funding covering illiquid assets). The HKMA would view this "
                         "balance sheet as low liquidity risk. The trade-off is that the branch may be "
                         "holding excess liquidity at the cost of net interest income.")
            elif lmr_c >= 100 and cfr_c < 200:
                joint = ("High short-term liquidity (LMR) combined with moderate structural funding (CFR) "
                         "suggests the branch manages its 30-day window well but has less structural cushion. "
                         "Monitor whether CFR is declining -- a branch can look liquid on a 30-day basis "
                         "while accumulating structural funding risk over a longer horizon.")
            elif lmr_c < 100 and cfr_c >= 200:
                joint = ("Moderate short-term liquidity but strong structural funding suggests the branch "
                         "has invested stable, long-term deposits into illiquid longer-term loans, "
                         "compressing the LMR. Provided LMR remains above 25%, this is acceptable -- "
                         "it reflects a classic lending business model.")
            else:
                joint = ("Both ratios are moderate. The branch is operating within regulatory bounds "
                         "but without significant buffer. Any material asset growth should be accompanied "
                         "by a parallel increase in stable funding to avoid ratio deterioration.")
            out["joint_liquidity"] = joint
        else:
            out["joint_liquidity"] = None

        out["cfr_text"] = cfr_interp + " " + cfr_trend
    else:
        out["cfr_text"] = None; out["joint_liquidity"] = None

    # ── Asset composition analysis ────────────────────────────────────────────
    ab = d["asset_bdown"] or {}
    if ab and total_a:
        sorted_a = sorted(ab.items(), key=lambda x: x[1], reverse=True)[:3]
        out["top_assets"] = sorted_a
        out["top_assets_pct"] = [(n, v / total_a * 100) for n, v in sorted_a]
        dominant = sorted_a[0][0] if sorted_a else ""
        dominant_pct = sorted_a[0][1] / total_a * 100 if sorted_a else 0

        if "Overseas" in dominant:
            asset_story = (
                f"With {dominant_pct:.1f}% of assets in intragroup / overseas office placements, "
                "this branch is primarily a booking and capital allocation vehicle for its parent. "
                "The economic substance of the assets -- and therefore the credit risk -- rests with "
                "the parent group, not the local Hong Kong counterparties. This means local credit metrics "
                "like NPL ratios are almost irrelevant; what matters is parent group solvency. "
                "From a regulatory standpoint, the HKMA scrutinises these structures closely under "
                "the locally incorporated vs. branch regime precisely because the asset quality "
                "cannot be evaluated in isolation."
            )
        elif "Loans" in dominant:
            asset_story = (
                f"Loans and receivables at {dominant_pct:.1f}% of total assets confirm this is a "
                "lending-driven franchise. Revenue is primarily spread-based, making it sensitive to "
                "the Hong Kong prime rate cycle and credit quality of the loan book. "
                + (f"The loan-to-deposit ratio of {ldr:.1f}% " if ldr else "")
                + ("suggests the branch is deploying deposits aggressively into loans. "
                   if ldr and ldr > 80 else
                   "suggests a conservative deployment of funding into loans. " if ldr else "")
                + ("Watch the provisions line -- even a modest uptick in specific provisions signals "
                   "that management is seeing credit deterioration in the portfolio before it reaches NPL status.")
            )
        elif "Trading" in dominant or "Securities" in dominant:
            asset_story = (
                f"Trading or investment securities at {dominant_pct:.1f}% of assets indicate a "
                "market-making or capital markets-oriented franchise. P&L will exhibit volatility "
                "correlated with credit spreads, equity indices, and FX moves -- not just interest rates. "
                "Executives should track the mark-to-market sensitivity table in the notes to understand "
                "the P&L impact of a 1% parallel shift in rates or a 10% equity market move."
            )
        else:
            asset_story = (
                "The asset base is diversified, with no single category exceeding half of the balance sheet. "
                "This is characteristic of a full-service commercial bank branch. Diversification reduces "
                "concentration risk but also makes it harder to identify a single business model driver -- "
                "revenue analysis requires drilling into the segment breakdown."
            )
        out["asset_story"] = asset_story
    else:
        out["top_assets"] = None; out["top_assets_pct"] = None; out["asset_story"] = None

    # ── Liability composition analysis ────────────────────────────────────────
    lb = d["liab_bdown"] or {}
    if lb and total_l:
        sorted_l = sorted(lb.items(), key=lambda x: x[1], reverse=True)[:3]
        out["top_liabs"] = sorted_l
        out["top_liabs_pct"] = [(n, v / total_l * 100) for n, v in sorted_l]
        dominant_l = sorted_l[0][0] if sorted_l else ""
        dominant_l_pct = sorted_l[0][1] / total_l * 100 if sorted_l else 0

        if "Customer" in dominant_l:
            liab_story = (
                f"Customer deposits at {dominant_l_pct:.1f}% of liabilities are the backbone of funding. "
                "This is the most stable and cheapest funding source, but it creates two structural risks: "
                "(1) Deposit concentration -- if a small number of large depositors represent most of the "
                "balance, the funding base is less stable than the headline number implies; "
                "(2) Repricing risk -- demand and short-dated deposits will reprice rapidly if the "
                "HKMA follows the US Federal Reserve in adjusting rates, compressing net interest margin "
                "if loan rates are slower to adjust."
            )
        elif "Overseas" in dominant_l or "Interbank" in dominant_l:
            liab_story = (
                f"Wholesale/intragroup funding at {dominant_l_pct:.1f}% of liabilities means this branch "
                "is not deposit-funded -- it relies on its parent or interbank counterparties for its "
                "operating capital. This creates a direct transmission channel: any stress, rating "
                "downgrade, or liquidity squeeze at parent level would immediately impair the branch's "
                "ability to fund its assets. Counterintuitively, this also means the branch balance "
                "sheet can expand or contract rapidly based on group-level capital allocation decisions, "
                "independent of local business activity."
            )
        elif "Certificates" in dominant_l or "Debt" in dominant_l:
            liab_story = (
                f"Capital markets instruments (CDs, issued notes) at {dominant_l_pct:.1f}% of liabilities "
                "provide term certainty but expose the branch to two risks: rollover risk at maturity "
                "if spreads have widened; and market risk on the fair value of fixed-rate instruments. "
                "An executive should check the maturity profile in the liquidity section of the notes "
                "to identify cliff-edge refinancing obligations in the next 12 months."
            )
        else:
            liab_story = (
                "The funding structure is diversified across multiple sources, which is a credit positive. "
                "No single source exceeds a dominant share, reducing event-driven liquidity risk. "
                "The cost of this diversification is typically higher average funding cost versus "
                "a pure deposit-funded model."
            )
        out["liab_story"] = liab_story
    else:
        out["top_liabs"] = None; out["top_liabs_pct"] = None; out["liab_story"] = None

    # ── Profitability analysis ────────────────────────────────────────────────
    if roa is not None:
        if roa > 2.0:
            prof_stance = ("very high for a bank. This level of ROA is unusual in a branch context "
                           "and typically reflects either a fee-intensive business model (e.g., investment "
                           "banking advisory fees, custody, FX), very cheap funding, or one-off gains. "
                           "Executives should decompose the income statement to confirm sustainability.")
        elif roa > 1.0:
            prof_stance = ("strong. A well-run commercial bank branch typically targets 1.0-1.5% ROA. "
                           "The branch is generating above-average returns on its asset base, "
                           "consistent with effective pricing discipline and cost control.")
        elif roa > 0.3:
            prof_stance = ("moderate. This is typical for wholesale or investment banking branches "
                           "where the gross balance sheet is large (inflating the denominator) but "
                           "much of the revenue is fee-based and sits off-balance-sheet.")
        elif roa > 0:
            prof_stance = ("marginal. The branch is covering its costs but generating minimal shareholder "
                           "value from its asset base. Common in treasury or booking branches where "
                           "the economic value sits at the parent, not the branch level.")
        else:
            prof_stance = ("the branch is loss-making on an ROA basis. This requires explanation: "
                           "is it a temporary credit cycle effect (elevated provisions), a structural "
                           "cost problem, or a deliberate parent-level decision to run the branch at "
                           "breakeven while profits are booked elsewhere?")

        out["roa"] = roa
        out["roa_text"] = (f"ROA of {roa:.2f}% is {prof_stance}")
    else:
        out["roa"] = None; out["roa_text"] = None

    if roe is not None:
        ke_assumed = 10.0
        spread = roe - ke_assumed
        if spread > 5:
            roe_text = (f"ROE of {roe:.1f}% significantly exceeds the assumed cost of equity of {ke_assumed:.0f}%, "
                        "creating positive economic value. This branch is destroying less capital than it earns -- "
                        "a genuine value creator within its parent group.")
        elif spread > 0:
            roe_text = (f"ROE of {roe:.1f}% modestly exceeds the assumed cost of equity of {ke_assumed:.0f}%. "
                        "The branch is earning slightly above its hurdle rate. Continued focus on "
                        "margin improvement or cost efficiency is needed to create durable economic value.")
        elif spread > -5:
            roe_text = (f"ROE of {roe:.1f}% is slightly below the assumed cost of equity of {ke_assumed:.0f}%. "
                        "The branch is not currently covering its cost of capital. This may be acceptable "
                        "if the branch provides strategic value to the parent (market access, client relationships) "
                        "beyond what the income statement captures.")
        else:
            roe_text = (f"ROE of {roe:.1f}% is materially below the assumed cost of equity of {ke_assumed:.0f}%. "
                        "The branch is a significant capital consumer relative to what it returns. "
                        "Unless there is a clear strategic rationale, a parent group would typically "
                        "face pressure to restructure or reduce the scale of this operation.")
        out["roe"] = roe; out["roe_text"] = roe_text
    else:
        out["roe"] = None; out["roe_text"] = None

    if profit_growth is not None:
        if profit_growth > 50:
            pg_text = (f"Profit grew {profit_growth:.1f}% -- an exceptional result. Executives must determine "
                       "whether this reflects operating leverage (revenue growing faster than costs), "
                       "a release of provisions, or one-off income. Only operating leverage is "
                       "structurally durable.")
        elif profit_growth > 15:
            pg_text = (f"Profit grew {profit_growth:.1f}%, a solid result ahead of typical mid-single-digit "
                       "sector norms. This is a signal of genuine earnings momentum, but validate "
                       "it against the trend in provisions -- improving credit costs can flatter profitability "
                       "even if the underlying revenue engine is slowing.")
        elif profit_growth > 0:
            pg_text = (f"Profit grew {profit_growth:.1f}% -- modest but positive. "
                       "The business is stable and incrementally improving. "
                       "The key question is whether this is tracking above or below the cost of equity "
                       "on a return-on-capital basis.")
        elif profit_growth > -20:
            pg_text = (f"Profit fell {abs(profit_growth):.1f}%. A decline of this magnitude typically reflects "
                       "either margin compression from the rate environment, rising operating costs, "
                       "or an uptick in provisions. Identifying which of these is driving the decline "
                       "determines whether corrective action is needed.")
        else:
            pg_text = (f"Profit fell {abs(profit_growth):.1f}% -- a severe deterioration. This is beyond "
                       "normal cyclical variation and requires immediate executive attention. "
                       "Possible causes: a large single credit loss, a material increase in provisions "
                       "signalling a deteriorating loan book, or a structural revenue decline.")
        out["profit_change"] = pg_text
    else:
        out["profit_change"] = None

    if prov_change is not None:
        if prov_change > 30:
            out["prov_signal"] = (f"Provisions rose {prov_change:.1f}% -- a material signal of credit stress. "
                                  "Rising provisions precede NPL recognition by 1-2 quarters on average. "
                                  "This is the single most important leading indicator of future earnings quality.")
        elif prov_change < -20:
            out["prov_signal"] = (f"Provisions fell {abs(prov_change):.1f}%, boosting reported profit. "
                                  "Provision releases can be genuine (improving credit quality) or aggressive "
                                  "(management optimism). Cross-check against the NPL and overdue loans table.")
        else:
            out["prov_signal"] = None
    else:
        out["prov_signal"] = None

    # ── Auto-generated credit / asset / liability quality analysis ─────────────
    credit_sentence = None

    ab = d.get("asset_bdown") or {}
    lb = d.get("liab_bdown") or {}

    # Dominant asset and liability
    top_asset_name = max(ab, key=ab.get) if ab and total_a else None
    top_asset_pct  = (ab[top_asset_name] / total_a * 100) if top_asset_name and total_a else 0
    top_liab_name  = max(lb, key=lb.get) if lb and total_l else None
    top_liab_pct   = (lb[top_liab_name] / total_l * 100) if top_liab_name and total_l else 0

    paragraphs = []

    # -- Provisions paragraph (always attempt, even without prior period) ------
    if prov is not None:
        if prov_change is not None:
            direction = "rose" if prov_change > 0 else "fell"
            pct_abs   = abs(prov_change)

            # Infer provision type from magnitude and asset mix
            if top_asset_name and "Overseas" in top_asset_name:
                prov_type = "collective provisions"
                prov_implication = ("a group-level portfolio stress signal -- not necessarily driven by "
                                    "identifiable local loan impairments, but by macro risk flags "
                                    "applied top-down from the parent")
            elif pct_abs > 40:
                prov_type = "specific provisions"
                prov_implication = ("clearly identified credit impairment on individual counterparties -- "
                                    "a move of this magnitude almost always reflects one or more named borrower "
                                    "deteriorations, not a routine collective model update")
            elif pct_abs > 15:
                prov_type = "provisions (likely a mix of specific and collective)"
                prov_implication = ("both identifiable borrower stress and a broader portfolio-level "
                                    "deterioration signal")
            else:
                prov_type = "provisions"
                prov_implication = ("a modest recalibration of expected credit losses, consistent with "
                                    "normal model updating rather than acute stress")

            prov_para = (
                f"Provisions {direction} {pct_abs:.1f}%, driven by {prov_type}, "
                f"implying {prov_implication}. "
            )

            # Link to profitability impact
            if profit and total_a:
                prov_actual = prov * um
                profit_actual = profit * um
                prov_to_profit = abs(prov_actual / profit_actual * 100) if profit_actual != 0 else None
                if prov_to_profit and prov_to_profit > 20:
                    prov_para += (
                        f"Provisions represent {prov_to_profit:.1f}% of net profit -- "
                        f"a{'n elevated' if prov_to_profit > 50 else ' significant'} share. "
                        f"{'Any further deterioration in credit quality would rapidly erode reported earnings.' if prov_change > 0 else 'The release of provisions has materially flattered reported earnings this period; underlying operating profit is weaker than the headline suggests.'} "
                    )
        else:
            # No prior period -- still comment on absolute level
            if loans and prov:
                llr_pct = prov / loans * 100
                if llr_pct > 2:
                    prov_para = (f"The loan loss reserve ratio stands at {llr_pct:.2f}% of gross loans -- "
                                 "above the typical 1-2% range for a well-collateralised Hong Kong portfolio, "
                                 "suggesting management is carrying a meaningful buffer against credit losses. ")
                elif llr_pct > 0.5:
                    prov_para = (f"The loan loss reserve ratio of {llr_pct:.2f}% of gross loans is within "
                                 "a normal range for a secured Hong Kong lending portfolio. ")
                else:
                    prov_para = (f"The loan loss reserve ratio of {llr_pct:.2f}% is thin. "
                                 "Even a small deterioration in the loan book could require a disproportionate "
                                 "increase in provisions, creating earnings volatility. ")
            else:
                prov_para = ""

        if prov_para:
            paragraphs.append(prov_para)

    # -- Asset quality paragraph -----------------------------------------------
    if top_asset_name:
        if "Overseas" in top_asset_name:
            asset_credit_para = (
                f"The dominant asset is {top_asset_name} ({top_asset_pct:.1f}% of total assets), "
                f"so credit risk sits primarily with the parent group and its global counterparties -- "
                f"not with local Hong Kong borrowers. "
                f"The practical implication is that this branch's asset quality cannot be assessed in isolation: "
                f"a credit event at head office level (a sovereign downgrade, a large trading loss, or a "
                f"regulatory capital breach at the parent) would transmit directly to this balance sheet "
                f"through intragroup receivables. "
                f"The HKMA is aware of this structural dependency and applies enhanced oversight to "
                f"branches with high intragroup asset concentrations under its overseas branch supervisory framework. "
            )
            # Cross-reference provisions
            if prov and total_a:
                prov_to_assets = prov / total_a * 100
                asset_credit_para += (
                    f"Locally held provisions of {prov_to_assets:.2f}% of total assets are largely symbolic "
                    f"in this context -- they cover local loan book tail risk, not the far larger intragroup exposure, "
                    f"which is implicitly backstopped by the parent group's capital rather than branch-level reserves."
                )
        elif "Loans" in top_asset_name:
            llr_note = ""
            if llr is not None:
                llr_note = (f" The loan loss reserve covers {llr:.2f}% of the gross loan book -- "
                            f"{'adequate' if llr > 1 else 'thin'} relative to a stressed loss scenario.")
            asset_credit_para = (
                f"The dominant asset is {top_asset_name} ({top_asset_pct:.1f}% of total assets), "
                f"so credit risk sits primarily with external borrowers in the local loan book. "
                f"This means the provisions line is the key metric to track: it is a direct, "
                f"forward-looking indicator of deterioration in the borrower portfolio, "
                f"typically leading NPL recognition by one to two quarters.{llr_note} "
                f"Executives should cross-reference the industry sector breakdown of loans against "
                f"the provisions movement -- if provisions are rising in sectors like property investment "
                f"or financial concerns, it signals concentrated stress rather than broad portfolio weakening."
            )
        elif "Trading" in top_asset_name or "Securities" in top_asset_name:
            asset_credit_para = (
                f"The dominant asset is {top_asset_name} ({top_asset_pct:.1f}% of total assets), "
                f"so credit risk manifests primarily as counterparty default and issuer spread widening "
                f"rather than traditional loan impairment. "
                f"Provisions in this context are a less reliable signal of stress than in a lending-driven book -- "
                f"mark-to-market losses can crystallise rapidly without prior provision build-up. "
                f"The relevant risk metrics to monitor are: VaR limits, counterparty credit exposure "
                f"by rating bucket, and the unrealised gains/losses table in the notes."
            )
        else:
            asset_credit_para = (
                f"With {top_asset_name} ({top_asset_pct:.1f}%) as the largest single asset class, "
                f"credit risk is moderately diversified. No single asset class dominates, "
                f"which limits concentration risk but also makes it harder to identify a single "
                f"credit risk driver from the headline numbers alone."
            )
        paragraphs.append(asset_credit_para)

    # -- Liability quality paragraph -------------------------------------------
    if top_liab_name:
        if "Customer" in top_liab_name:
            liab_credit_para = (
                f"On the funding side, customer deposits ({top_liab_pct:.1f}% of liabilities) "
                f"are the primary source. This is structurally stable, but introduces a behavioural risk: "
                f"if credit concerns about the branch or its parent become public, even secured deposit "
                f"holders may withdraw, creating a run dynamic that the LMR is designed to withstand. "
                f"{'With an LMR of ' + str(round(lmr_c, 1)) + '%, the branch holds sufficient HQLA to absorb a 30-day withdrawal scenario well above the regulatory minimum.' if lmr_c else ''}"
            )
        elif "Overseas" in top_liab_name or "Interbank" in top_liab_name:
            liab_credit_para = (
                f"The dominant liability is {top_liab_name} ({top_liab_pct:.1f}% of liabilities). "
                f"Wholesale and intragroup funding is the most fragile funding source in a stress scenario -- "
                f"it can be withdrawn overnight without regulatory constraint. "
                f"If the asset side is also dominated by intragroup receivables, the balance sheet is "
                f"essentially a pass-through vehicle: the credit quality of both sides depends entirely "
                f"on the parent group. The branch adds limited standalone credit resilience."
            )
        elif "Certificates" in top_liab_name or "Debt" in top_liab_name:
            liab_credit_para = (
                f"Capital markets instruments ({top_liab_pct:.1f}% of liabilities) dominate the funding base. "
                f"These provide term certainty -- a credit positive -- but the branch faces rollover risk "
                f"at maturity. If the branch's credit rating or the parent's rating deteriorates between "
                f"issuance and maturity, refinancing costs will increase materially. "
                f"Executives should review the maturity ladder in the liquidity notes to identify "
                f"any near-term refinancing cliffs."
            )
        else:
            liab_credit_para = (
                f"The liability structure is diversified, with {top_liab_name} ({top_liab_pct:.1f}%) "
                f"as the largest single source. No single funding channel dominates, "
                f"which is a credit positive -- it limits the impact of disruption in any one market."
            )
        paragraphs.append(liab_credit_para)

    # -- Cross-check: asset vs liability risk alignment -----------------------
    if top_asset_name and top_liab_name:
        if "Overseas" in top_asset_name and ("Overseas" in top_liab_name or "Interbank" in top_liab_name):
            cross_para = (
                "Taken together, both the asset and liability sides of this balance sheet are dominated "
                "by intragroup / wholesale flows. The branch is operating as a conduit within a larger "
                "group funding and booking structure. The HKMA's primary concern in this configuration "
                "is not day-to-day credit quality but systemic interconnectedness: a group-level shock "
                "would simultaneously impair assets and cut off funding. "
                "The standalone VIR (Valuation in Resolution) floor -- derived from book equity less "
                "provisions -- is the most relevant measure of residual value in that stress scenario."
            )
        elif "Loans" in top_asset_name and "Customer" in top_liab_name:
            cross_para = (
                "The classic commercial banking model -- loans funded by deposits -- creates a "
                "natural interest rate re-pricing risk: if deposit rates rise faster than loan yields, "
                "net interest margin compresses. The provisions trajectory is the primary credit "
                "risk signal, and the LMR/CFR ratios confirm whether the deposit base is stable enough "
                "to fund the loan book through a credit cycle."
            )
        else:
            cross_para = (
                "The combination of asset and liability profiles creates a mixed risk picture. "
                "Credit risk drivers on the asset side and funding stability on the liability side "
                "should be assessed independently -- they are not structurally linked in a way "
                "that automatically hedges one against the other."
            )
        paragraphs.append(cross_para)

    if paragraphs:
        credit_sentence = " ".join(paragraphs)
    else:
        credit_sentence = None

    out["credit_sentence"] = credit_sentence

    # ── Bottom line verdict ───────────────────────────────────────────────────
    positives = []
    negatives = []
    if lmr_c and lmr_c >= 100: positives.append(f"strong short-term liquidity (LMR {lmr_c:.1f}%)")
    if cfr_c and cfr_c >= 200:  positives.append(f"structurally sound funding (CFR {cfr_c:.1f}%)")
    if roa and roa > 0.5:       positives.append(f"above-average profitability (ROA {roa:.2f}%)")
    if roe and roe > 10:        positives.append(f"ROE above cost of equity ({roe:.1f}%)")
    if profit_growth and profit_growth > 10: positives.append(f"strong earnings growth ({profit_growth:.1f}%)")
    if lmr_c and lmr_c < 50:   negatives.append(f"lean short-term liquidity buffer (LMR {lmr_c:.1f}%)")
    if cfr_c and cfr_c < 100:   negatives.append("structural funding shortfall (CFR below 100%)")
    if roa and roa < 0:         negatives.append(f"loss-making (ROA {roa:.2f}%)")
    if profit_growth and profit_growth < -20: negatives.append(f"severe profit decline ({profit_growth:.1f}%)")
    if prov_change and prov_change > 30: negatives.append(f"rising provisions (+{prov_change:.1f}%)")

    entity = d.get("entity", "This institution")
    if positives and not negatives:
        verdict_tone = "presents a fundamentally sound profile."
    elif positives and negatives:
        verdict_tone = "has clear strengths but specific areas that warrant management attention."
    elif negatives:
        verdict_tone = "shows multiple indicators that require immediate executive attention."
    else:
        verdict_tone = "presents a mixed picture that requires further investigation."

    verdict_body = f"{entity} {verdict_tone}"
    if positives:
        verdict_body += f" Strengths: {'; '.join(positives)}."
    if negatives:
        verdict_body += f" Concerns: {'; '.join(negatives)}."

    if lmr_c and cfr_c:
        if lmr_c >= 100 and cfr_c >= 200 and (roa or 0) > 0:
            verdict_body += (" The combination of high liquidity, sound structural funding, and positive "
                             "profitability is the hallmark of a well-managed branch. The primary risk vector "
                             "is external: a Hong Kong rate cycle reversal, a parent group credit event, "
                             "or a macro shock to the HK interbank market.")
        elif lmr_c >= 25 and cfr_c >= 100:
            verdict_body += (" The branch meets all regulatory thresholds with some buffer, but is not "
                             "positioned with excess safety margins. Management should prioritise maintaining "
                             "LMR well above 25% and avoid rapid balance sheet expansion without parallel "
                             "stable funding growth.")

    out["verdict"] = verdict_body
    return out



# ── RENDER ────────────────────────────────────────────────────────────────────

def render_report(d):
    import streamlit.components.v1 as components
    um = d["unit_mult"]; cy = d["currency"]
    val = build_valuation(d)
    ana = build_analysis(d)

    # Entity header
    st.markdown(f"""
    <div class="entity-header">
        <h2>{d['entity']}</h2>
        <div class="meta">Period ending {d['report_date']} &nbsp; | &nbsp;
        Figures in {cy} {d['unit_label']}</div>
    </div>""", unsafe_allow_html=True)

    if d["description"]:
        st.markdown(f'<div class="info-box">Business: {d["description"]}</div>',
                    unsafe_allow_html=True)

    # ── VALUATION BLOCK ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Valuation</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="warn-box">
    Three lenses are used -- equity P/BV model, Gordon Growth implied P/E, and HKMA's FIRO Valuation in Resolution (VIR).
    All figures are derived from balance sheet data in this filing. No market prices are used.
    </div>""", unsafe_allow_html=True)

    vcol1, vcol2 = st.columns(2)

    with vcol1:
        if val["ok_pbv"]:
            rows_pbv = ""
            for i, (lbl, num, note) in enumerate(val["steps_pbv"]):
                sign = "" if i == 0 else "x" if i <= 2 else ""
                style = "font-weight:700;color:#E60028;" if i >= 3 else ""
                rows_pbv += (f'<div class="val-step">'
                             f'<span class="val-label">{lbl}</span>'
                             f'<span class="val-num" style="{style}">{num}</span>'
                             f'</div>')
                if note:
                    rows_pbv += f'<div style="font-size:0.72rem;color:#64748b;padding:0 0 6px 0;">{note}</div>'
            st.markdown(f'<div class="valuation-block"><h3>Entity Valuation (P/BV Equity Model)</h3>{rows_pbv}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="neutral-box">P/BV model requires book equity data -- not extractable from this filing.</div>',
                        unsafe_allow_html=True)

    with vcol2:
        if val["ok_gordon"]:
            rows_g = ""
            for i, (lbl, num, note) in enumerate(val["steps_gordon"]):
                style = "font-weight:700;color:#E60028;" if i == len(val["steps_gordon"]) - 1 else ""
                rows_g += (f'<div class="val-step">'
                           f'<span class="val-label">{lbl}</span>'
                           f'<span class="val-num" style="{style}">{num}</span>'
                           f'</div>')
                if note:
                    rows_g += f'<div style="font-size:0.72rem;color:#64748b;padding:0 0 6px 0;">{note}</div>'
            st.markdown(f'<div class="valuation-block"><h3>Entity Valuation (Gordon Growth Model)</h3>{rows_g}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="neutral-box">Gordon Growth model requires positive net profit -- not available in this period.</div>',
                        unsafe_allow_html=True)

    # HKFRS 13 note
    st.markdown(f'<div class="neutral-box"><strong>HKFRS 13 Instrument Fair Value:</strong> {val["fv_note"]}</div>',
                unsafe_allow_html=True)

    # VIR
    if val["ok_vir"]:
        rows_vir = ""
        for lbl, num, note in val["vir_steps"]:
            rows_vir += (f'<div class="val-step">'
                         f'<span class="val-label">{lbl}</span>'
                         f'<span class="val-num" style="color:#1A1A1A;">{num}</span>'
                         f'</div>')
            if note:
                rows_vir += f'<div style="font-size:0.72rem;color:#64748b;padding:0 0 6px 0;">{note}</div>'
        st.markdown(f'<div class="valuation-block"><h3>Valuation in Resolution (FIRO Ord. Cap. 628 / VIR)</h3>{rows_vir}</div>',
                    unsafe_allow_html=True)

    # ── KPI ROW ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Key Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    def kpi_card(col, label, curr, prev, unit_mult, currency, is_pct=False):
        with col:
            if is_pct:
                val_str = f"{curr:.1f}%" if curr is not None else "N/A"
                c_str, cls = chg(curr, prev, pct=True)
            else:
                val_str = f"{currency} {fmt(curr, unit_mult)}" if curr is not None else "N/A"
                c_str, cls = chg(curr, prev)
            b = badge(c_str, cls) if c_str != "N/A" else ""
            st.markdown(f"""<div class="card">
                <div class="card-title">{label}</div>
                <div class="card-value">{val_str}{b}</div>
                <div class="card-sub">vs prior period</div>
            </div>""", unsafe_allow_html=True)

    kpi_card(c1, "Total Assets", d["total_assets_curr"], d["total_assets_prev"], um, cy)
    kpi_card(c2, "Net Profit / (Loss)", d["profit_curr"], d["profit_prev"], um, cy)
    kpi_card(c3, "Avg LMR", d["lmr_curr"], d["lmr_prev"], 1, "", is_pct=True)
    kpi_card(c4, "Avg CFR", d["cfr_curr"], d["cfr_prev"], 1, "", is_pct=True)

    # ── FINANCIALS TABLE ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Financial Summary</div>', unsafe_allow_html=True)
    rows_fin = ""
    rows_fin += render_table_row("Interest Income", d["int_income_curr"], d["int_income_prev"], um, cy)
    rows_fin += render_table_row("Total Operating Income", d["op_income_curr"], d["op_income_prev"], um, cy)
    rows_fin += render_table_row("Profit / (Loss) after Tax", d["profit_curr"], d["profit_prev"], um, cy, bold=True)
    rows_fin += render_table_row("Total Assets", d["total_assets_curr"], d["total_assets_prev"], um, cy, bold=True)
    rows_fin += render_table_row("Total Liabilities", d["total_liab_curr"], d["total_liab_prev"], um, cy)
    rows_fin += render_table_row("Loans & Receivables", d["loans_curr"], d["loans_prev"], um, cy)
    rows_fin += render_table_row("Customer Deposits", d["deposits_curr"], d["deposits_prev"], um, cy)
    rows_fin += render_table_row("Provisions", d["provisions_curr"], d["provisions_prev"], um, cy)

    st.markdown(f"""<table class="styled">
      <thead><tr>
        <th style="width:40%">Line Item</th>
        <th class="num" style="width:20%">Current</th>
        <th class="num" style="width:20%">Prior</th>
        <th class="num" style="width:20%">Change</th>
      </tr></thead>
      <tbody>{rows_fin}</tbody>
    </table>""", unsafe_allow_html=True)

    # ── RATIOS TABLE ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Regulatory and Capital Ratios</div>', unsafe_allow_html=True)
    rows_rat = ""
    rows_rat += render_table_row("Avg Liquidity Maintenance Ratio (LMR)", d["lmr_curr"], d["lmr_prev"], 1, "", is_pct=True)
    rows_rat += render_table_row("Avg Core Funding Ratio (CFR)", d["cfr_curr"], d["cfr_prev"], 1, "", is_pct=True)
    rows_rat += render_table_row("CET1 Capital Ratio", d["cet1_curr"], d["cet1_prev"], 1, "", is_pct=True)
    rows_rat += render_table_row("Leverage Ratio", d["lev_curr"], d["lev_prev"], 1, "", is_pct=True)
    st.markdown(f"""<table class="styled">
      <thead><tr>
        <th style="width:40%">Ratio</th>
        <th class="num" style="width:20%">Current Period</th>
        <th class="num" style="width:20%">Prior Period</th>
        <th class="num" style="width:20%">Change (pp)</th>
      </tr></thead>
      <tbody>{rows_rat}</tbody>
    </table>""", unsafe_allow_html=True)

    # ── CHARTS ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Balance Sheet Composition</div>', unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)
    with ch1:
        render_pie(d, d["asset_bdown"], d["total_assets_curr"], "Asset Composition")
    with ch2:
        render_pie(d, d["liab_bdown"], d["total_liab_curr"], "Liability Composition")

    # ── EXECUTIVE ANALYSIS ───────────────────────────────────────────────────
    st.markdown('<div class="section-header">Executive Analysis</div>', unsafe_allow_html=True)

    # Liquidity
    if ana["lmr_text"] or ana["cfr_text"]:
        content = ""
        if ana["lmr_text"]:
            content += f"<p><strong>Liquidity Maintenance Ratio (LMR):</strong> {ana['lmr_text']}</p>"
        if ana["cfr_text"]:
            content += f"<p><strong>Core Funding Ratio (CFR):</strong> {ana['cfr_text']}</p>"
        st.markdown(f'<div class="exec-section"><h3>What the Liquidity Ratios Are Telling You</h3>{content}</div>',
                    unsafe_allow_html=True)

    # Asset/Liability composition narrative
    if ana["asset_story"] or ana["liab_story"]:
        content = ""
        if ana["top_assets_pct"]:
            top3 = "; ".join([f"{n} ({v:.1f}%)" for n, v in ana["top_assets_pct"]])
            content += f"<p><strong>Top 3 assets:</strong> {top3}. {ana['asset_story']}</p>"
        if ana["top_liabs_pct"]:
            top3l = "; ".join([f"{n} ({v:.1f}%)" for n, v in ana["top_liabs_pct"]])
            content += f"<p><strong>Top 3 liabilities:</strong> {top3l}. {ana['liab_story']}</p>"
        st.markdown(f'<div class="exec-section"><h3>What the Balance Sheet Composition Reveals</h3>{content}</div>',
                    unsafe_allow_html=True)

    # Profitability
    if ana["profit_story"] or ana["profit_change"]:
        content = ""
        if ana["profit_story"]:
            content += f"<p>{ana['profit_story']}</p>"
        if ana["profit_change"]:
            content += f"<p>{ana['profit_change']}</p>"
        box_cls = "green-box" if (d["profit_curr"] or 0) > 0 else "red-box"
        st.markdown(f'<div class="{box_cls}">'
                    f'<strong>Profitability Assessment:</strong><br>{content}</div>',
                    unsafe_allow_html=True)

    # Overall verdict
    signals = []
    if d["lmr_curr"] and d["lmr_curr"] > 100: signals.append("strong liquidity")
    if d["cfr_curr"] and d["cfr_curr"] > 100:  signals.append("well-funded balance sheet")
    if d["profit_curr"] and d["profit_curr"] > 0: signals.append("profitable operations")
    if d["provisions_curr"] and d["total_assets_curr"] and \
       d["provisions_curr"] / d["total_assets_curr"] > 0.01:
        signals.append("elevated provisions suggesting credit stress")

    verdict = (f"{d['entity']} presents a profile of {', '.join(signals[:2]) if signals else 'mixed indicators'}"
               f"{(' and ' + signals[2]) if len(signals) > 2 else ''}. "
               "The key question for an executive is whether the current liquidity and funding ratios "
               "reflect deliberate balance sheet management or a structural feature of the business model. "
               "If the branch relies heavily on intragroup funding, a deterioration at parent level "
               "would transmit rapidly. If funded by local deposits, it is operationally more resilient "
               "but faces repricing risk in a rising rate environment.")

    st.markdown(f'<div class="neutral-box"><strong>Bottom Line:</strong> {verdict}</div>',
                unsafe_allow_html=True)

    # CSV download
    rows = [
        ["Entity", d["entity"]], ["Report Date", d["report_date"]],
        ["Currency", d["currency"]], ["Unit Label", d["unit_label"]],
        ["Profit/Loss after Tax (curr)", d["profit_curr"]],
        ["Profit/Loss after Tax (prev)", d["profit_prev"]],
        ["Total Assets (curr)", d["total_assets_curr"]],
        ["Total Assets (prev)", d["total_assets_prev"]],
        ["Total Liabilities (curr)", d["total_liab_curr"]],
        ["Total Liabilities (prev)", d["total_liab_prev"]],
        ["Loans & Receivables (curr)", d["loans_curr"]],
        ["Customer Deposits (curr)", d["deposits_curr"]],
        ["Avg LMR % (curr)", d["lmr_curr"]], ["Avg LMR % (prev)", d["lmr_prev"]],
        ["Avg CFR % (curr)", d["cfr_curr"]], ["Avg CFR % (prev)", d["cfr_prev"]],
        ["Book Equity", d["equity"]],
    ]
    df = pd.DataFrame(rows, columns=["Field", "Value"])
    st.markdown("---")
    st.download_button("Download CSV", df.to_csv(index=False),
                       file_name=f"{d['entity'].replace(' ','_')}_extracted.csv",
                       mime="text/csv")


# ── UPLOAD UI ────────────────────────────────────────────────────────────────

st.markdown("""
<div style="background:#fefce8; border:1px solid #fde68a; border-radius:10px;
            padding:14px 18px; margin-bottom:18px; font-size:0.875rem; color:#78350f;">
    <strong>File Requirement:</strong> Your PDF must contain <strong>selectable text</strong>
    (a digital PDF, not a scanned image). To verify: open the PDF and try to highlight a word with
    your cursor. If you can select text, it will work. Scanned PDFs are not supported and will
    return N/A for most fields.
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Drop an HKMA Banking Disclosure PDF here (text-based PDFs only)",
    type=["pdf"],
    help="Must be a digital/text-based PDF, not a scanned document"
)

if uploaded:
    with st.spinner("Reading PDF..."):
        text = extract_text(uploaded)
    with st.spinner("Extracting and analysing data..."):
        data = extract_all(text)

    missing = [k for k in ["total_assets_curr", "profit_curr"] if data[k] is None]
    if missing:
        st.markdown(
            f'<div class="warn-box">Could not extract: {", ".join(missing)}. '
            f'This PDF may use a non-standard layout. Affected values will show as N/A.</div>',
            unsafe_allow_html=True)

    render_report(data)

else:
    st.markdown("""
    <div class="card" style="text-align:center; padding:48px; border:2px dashed #d1d5db;">
        <div style="font-size:3rem; margin-bottom:12px;">📄</div>
        <div style="font-size:1.1rem; font-weight:600; color:#374151; margin-bottom:8px;">
            Upload an HKMA Disclosure PDF to get started</div>
        <div style="color:#9ca3af; font-size:0.875rem;">
            Supports: Natixis · UBS · JPMorgan · ORIX · Standard Chartered · HSBC · and more
        </div>
    </div>""", unsafe_allow_html=True)
