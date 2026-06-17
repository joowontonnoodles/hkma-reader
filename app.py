import io
import re
import streamlit as st
import pdfplumber
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="HKMA Disclosure Analyser", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Raleway','Arial',sans-serif; color: #1A1A1A; }
.stApp { background: #F5F5F5; }

.hero {
    background: #FFFFFF;
    border-bottom: 3px solid #E60028;
    padding: 28px 36px 20px;
    margin-bottom: 24px;
}
.hero h1 { color: #1A1A1A; font-size: 1.55rem; font-weight: 700; margin: 0 0 4px 0; }
.hero-sub { color: #6B6B6B; font-size: 0.86rem; margin: 0; }

.section-header {
    font-size: 0.66rem; font-weight: 700; color: #E60028;
    letter-spacing: 1.8px; text-transform: uppercase;
    border-bottom: 1px solid #E60028; padding-bottom: 6px; margin: 28px 0 14px;
}
.entity-header {
    background: #FFFFFF; border-left: 5px solid #E60028;
    padding: 18px 24px; margin-bottom: 18px;
}
.entity-header h2 { margin: 0; font-size: 1.25rem; font-weight: 700;
    text-transform: uppercase; color: #1A1A1A; }
.entity-header .meta { font-size: 0.78rem; color: #6B6B6B; margin-top: 4px; }

.card {
    background: #FFFFFF; border-top: 3px solid #E60028;
    padding: 16px 18px; margin-bottom: 14px;
}
.card-title { font-size: 0.63rem; font-weight: 700; letter-spacing: 1.4px;
    text-transform: uppercase; color: #6B6B6B; margin-bottom: 5px; }
.card-value { font-size: 1.4rem; font-weight: 700; color: #1A1A1A; }
.card-sub { font-size: 0.73rem; color: #6B6B6B; margin-top: 2px; }

.badge-up { display:inline-block; background:#E60028; color:#FFFFFF;
    font-size:0.63rem; font-weight:700; padding:2px 6px; border-radius:2px; margin-left:5px; }
.badge-dn { display:inline-block; background:#1A1A1A; color:#FFFFFF;
    font-size:0.63rem; font-weight:700; padding:2px 6px; border-radius:2px; margin-left:5px; }
.badge-nt { display:inline-block; background:#D9D9D9; color:#6B6B6B;
    font-size:0.63rem; font-weight:700; padding:2px 6px; border-radius:2px; margin-left:5px; }

.info-box {
    background: #FFFFFF; border-left: 3px solid #E60028;
    padding: 10px 14px; font-size: 0.85rem; color: #1A1A1A;
    margin-bottom: 12px; line-height: 1.6;
}
.neutral-box {
    background: #F5F5F5; border-left: 3px solid #D9D9D9;
    padding: 12px 15px; font-size: 0.85rem; color: #1A1A1A;
    margin-bottom: 12px; line-height: 1.7;
}
.analysis-box {
    background: #FFFFFF; border-top: 2px solid #E60028;
    padding: 20px 24px; margin-bottom: 14px;
}
.analysis-box h3 {
    font-size: 0.66rem; font-weight: 700; color: #E60028;
    text-transform: uppercase; letter-spacing: 1.4px; margin: 0 0 10px 0;
}
.analysis-box p { font-size: 0.85rem; color: #1A1A1A; line-height: 1.75; margin: 0 0 8px 0; }

table.styled { width:100%; border-collapse:collapse; font-size:0.84rem; }
table.styled th {
    background: #1A1A1A; color: #FFFFFF; padding: 8px 12px;
    text-align: left; font-weight: 700; font-size: 0.68rem;
    letter-spacing: 0.8px; text-transform: uppercase;
}
table.styled td {
    padding: 8px 12px; border-bottom: 1px solid #D9D9D9;
    color: #1A1A1A; background: #FFFFFF;
}
table.styled tr:last-child td { border-bottom: none; }
table.styled tr:hover td { background: #F5F5F5; }
.num { text-align:right !important; font-variant-numeric: tabular-nums; }
.bold-row td { font-weight: 700; background: #F5F5F5 !important; }

.conc-item {
    display: flex; align-items: baseline; gap: 10px;
    padding: 6px 0; border-bottom: 1px solid #F0F0F0;
    font-size: 0.84rem;
}
.conc-item:last-child { border-bottom: none; }
.conc-rank { color: #E60028; font-weight: 700; min-width: 18px; }
.conc-name { flex: 1; color: #1A1A1A; }
.conc-pct  { color: #1A1A1A; font-weight: 600; min-width: 52px; text-align: right; }
.conc-val  { color: #6B6B6B; font-size: 0.78rem; min-width: 80px; text-align: right; }
</style>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>HKMA Financial Disclosure Analyser</h1>
  <p class="hero-sub">Upload any HKMA Banking Disclosure PDF. Branches, locally incorporated banks, and restricted licence banks.</p>
</div>
""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────

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
    r"limited\s+liability|www\.|http|copyright|all\s+rights|"
    r"\d+\s*$)",
    re.IGNORECASE
)


def extract_entity_name(text: str) -> str:
    candidates = []
    for line in text.split("\n")[:40]:
        line = line.strip()
        if not line or len(line) < 4 or len(line) > 120:
            continue
        if JUNK.match(line):
            continue
        if re.search(r"\d{4}", line) and "bank" not in line.lower():
            continue
        score = 0
        if re.search(r"bank|limited|ltd|plc|branch|corp|financial", line, re.I):
            score += 3
        if line[0].isupper():
            score += 1
        if len(line) > 10:
            score += 1
        candidates.append((score, line))
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1] if candidates else "Unknown Entity"


def parse_num(s: str, unit_mult: float) -> float:
    s = s.replace(",", "").replace(" ", "")
    try:
        return float(s) * unit_mult
    except ValueError:
        return None


def detect_unit(text: str):
    t = text[:3000]
    if re.search(r"HKD?\s*(?:thousand|'000|000s)", t, re.I):
        return 1_000, "thousands"
    if re.search(r"HKD?\s*(?:billion)", t, re.I):
        return 1_000_000_000, "billions"
    if re.search(r"HKD?\s*(?:million|mn|mln)", t, re.I):
        return 1_000_000, "millions"
    if re.search(r"(?:thousand|'000)", t, re.I):
        return 1_000, "thousands"
    return 1_000_000, "millions"


def detect_currency(text: str) -> str:
    for pat, cur in [
        (r"\bHKD\b|Hong Kong Dollars?", "HKD"),
        (r"\bUSD\b|US Dollars?", "USD"),
        (r"\bGBP\b|Pounds? Sterling", "GBP"),
        (r"\bCNY\b|RMB|Renminbi", "CNY"),
    ]:
        if re.search(pat, text[:2000], re.I):
            return cur
    return "HKD"


def find_two_values(text: str, patterns: list, unit_mult: float = 1.0):
    NEG = r"(?:\(([\d,]+\.?\d*)\)|-(([\d,]+\.?\d*)))"
    POS = r"([\d,]+\.?\d*)"
    NUM = r"(?:\(([\d,]+\.?\d*)\)|(-?[\d,]+\.?\d*))"
    for pat in patterns:
        for full_pat in [
            pat + r"[^\d\n()]{0,60}" + NUM + r"[^\d\n()]{0,60}" + NUM,
            pat + r"[^\d\n()]{0,80}" + POS + r"[^\d\n()]{0,80}" + POS,
        ]:
            m = re.search(full_pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                g = [x for x in m.groups() if x is not None]
                if len(g) >= 2:
                    v1 = parse_num(g[0], unit_mult)
                    v2 = parse_num(g[1], unit_mult)
                    if v1 and v1 > 0:
                        return v1, v2
        m = re.search(pat + r"[^\d\n()]{0,80}" + POS, text, re.IGNORECASE)
        if m:
            v1 = parse_num(m.group(1), unit_mult)
            if v1 and v1 > 0:
                return v1, None
    return None, None


ASSET_PATTERNS = [
    ("Cash and Balances with Banks",
     r"cash\s+and\s+(?:balances?\s+(?:with|at)\s+banks?|short[- ]term\s+funds?)"),
    ("Exchange Fund / Central Bank",
     r"(?:amount\s+due\s+from\s+exchange\s+fund|exchange\s+fund\s+bills?|"
     r"balances?\s+with\s+central\s+bank|due\s+from\s+(?:hkma|central\s+bank))"),
    ("Amount Due from Overseas Offices",
     r"(?:amount\s+due\s+from\s+overseas|due\s+from\s+(?:head\s+office|parent|overseas))"),
    ("Loans and Receivables",
     r"(?:loans?\s+and\s+(?:receivables?|advances?(?:\s+to\s+customers?)?)|"
     r"advances?\s+to\s+customers?)"),
    ("Investment Securities",
     r"(?:investment\s+securities|financial\s+assets?\s+(?:at\s+)?(?:fair\s+value|amortised)|"
     r"debt\s+securities?|available[- ]for[- ]sale|held[- ]to[- ]maturity)"),
    ("Trading Assets",
     r"trading\s+(?:assets?|securities?|book)"),
    ("Interbank Placements",
     r"(?:inter[- ]?bank|placement[s]?\s+with\s+banks?|due\s+from\s+banks?)"),
    ("Other Assets",
     r"other\s+assets?(?:\s+and\s+receivables?)?"),
    ("Property and Equipment",
     r"(?:property|plant\s+and\s+equipment|right[- ]of[- ]use|investment\s+propert)"),
]

LIAB_PATTERNS = [
    ("Customer Deposits",
     r"deposits?\s+from\s+customers?|customer\s+deposits?"),
    ("Interbank Deposits",
     r"(?:deposits?\s+(?:and\s+balances?\s+)?from\s+banks?|due\s+to\s+banks?|"
     r"inter[- ]?bank\s+(?:deposits?|borrowings?))"),
    ("Amount Due to Overseas Offices",
     r"(?:amount\s+due\s+to\s+overseas|due\s+to\s+(?:head\s+office|parent|overseas))"),
    ("Exchange Fund / Central Bank Liabilities",
     r"(?:amount\s+due\s+to\s+exchange\s+fund|due\s+to\s+(?:hkma|central\s+bank))"),
    ("Certificates of Deposit / Debt Issued",
     r"(?:certificates?\s+of\s+deposit|debt\s+(?:securities?\s+)?issued|"
     r"notes?\s+issued|bonds?\s+issued)"),
    ("Trading Liabilities",
     r"trading\s+liabilit"),
    ("Other Liabilities",
     r"other\s+liabilit"),
    ("Subordinated Debt",
     r"subordinated"),
]


def extract_breakdown(text: str, patterns: list, unit_mult: float) -> dict:
    result = {}
    for label, pat in patterns:
        m = re.search(
            pat + r"[^\n\d()]{0,60}([\d,]+\.?\d*)",
            text, re.IGNORECASE
        )
        if m:
            val = parse_num(m.group(1), unit_mult)
            if val and val > 0:
                result[label] = val
    return result


def extract_all(text: str) -> dict:
    unit_mult, unit_label = detect_unit(text)
    currency = detect_currency(text)
    entity = extract_entity_name(text)

    date_m = re.search(
        r"(?:as\s+(?:at|of)|for\s+the\s+(?:year|period)\s+ended?)\s+"
        r"(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}|"
        r"december\s+31,?\s+\d{4}|31\s+december\s+\d{4}|31\s+march\s+\d{4})",
        text, re.IGNORECASE
    )
    report_date = date_m.group(1).title() if date_m else "N/A"

    profit_curr, profit_prev = find_two_values(text, [
        r"profit\s+after\s+tax(?:ation)?",
        r"(?:net\s+)?(?:profit|income|loss)\s+(?:for\s+the\s+year|after\s+tax)",
        r"loss\s+for\s+the\s+year",
    ], unit_mult)
    if profit_curr is None:
        profit_curr, profit_prev = find_two_values(text, [
            r"profit\s+before\s+tax(?:ation)?",
        ], unit_mult)

    op_income_curr, op_income_prev = find_two_values(text, [
        r"total\s+operating\s+income", r"operating\s+income",
        r"net\s+operating\s+income",
    ], unit_mult)
    int_income_curr, int_income_prev = find_two_values(text, [
        r"interest\s+income(?:\s+calculated)?", r"total\s+interest\s+income",
    ], unit_mult)
    total_assets_curr, total_assets_prev = find_two_values(text, [
        r"total\s+assets"
    ], unit_mult)
    total_liab_curr, total_liab_prev = find_two_values(text, [
        r"total\s+liabilit"
    ], unit_mult)
    loans_curr, loans_prev = find_two_values(text, [
        r"loans?\s+and\s+(?:receivables?|advances?(?:\s+to\s+customers?)?)",
        r"advances?\s+to\s+customers?",
    ], unit_mult)
    deposits_curr, deposits_prev = find_two_values(text, [
        r"deposits?\s+from\s+customers?",
        r"customer\s+deposits?",
    ], unit_mult)

    # Provisions: standard then impairment variants
    spec_curr, spec_prev = find_two_values(text, [
        r"specific\s+provisions?",
        r"individually\s+(?:assessed|impaired)",
    ], unit_mult)
    coll_curr, coll_prev = find_two_values(text, [
        r"collective\s+provisions?",
        r"collectively\s+(?:assessed|impaired)",
        r"portfolio\s+provisions?",
    ], unit_mult)
    total_prov_curr, total_prov_prev = find_two_values(text, [
        r"total\s+provisions?",
        r"(?:^|\s)provisions?\b",
    ], unit_mult)
    if total_prov_curr is None and spec_curr is not None:
        total_prov_curr = (spec_curr or 0) + (coll_curr or 0)
        total_prov_prev = ((spec_prev or 0) + (coll_prev or 0)) if spec_prev or coll_prev else None
    if total_prov_curr is None:
        ci_curr, ci_prev = find_two_values(text, [
            r"credit\s+impairment\s+charges",
            r"impairment\s+(?:charge|loss)(?:es)?",
        ], unit_mult)
        if ci_curr is None:
            rel_curr, rel_prev = find_two_values(text, [
                r"credit\s+impairment\s+releases?"
            ], unit_mult)
            if rel_curr is not None:
                total_prov_curr = -rel_curr
                total_prov_prev = (-rel_prev) if rel_prev else None
        else:
            total_prov_curr = ci_curr
            total_prov_prev = ci_prev

    # LMR
    lmr_curr, lmr_prev = None, None
    for pat in [
        r"average\s+liquidity\s+maintenance\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        r"average\s+(?:liquidity\s+maintenance|LMR)[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        r"average\s+liquidity\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            lmr_curr = float(m.group(1))
            lmr_prev = float(m.group(2))
            break
    if lmr_curr is None:
        m = re.search(
            r"average\s+liquidity\s+(?:maintenance\s+)?ratio[^\d]{0,60}([\d.]+)\s*%",
            text, re.IGNORECASE
        )
        if m:
            lmr_curr = float(m.group(1))

    # CFR
    cfr_curr, cfr_prev = None, None
    m = re.search(
        r"average\s+core\s+funding\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        text, re.IGNORECASE
    )
    if m:
        cfr_curr = float(m.group(1))
        cfr_prev = float(m.group(2))
    else:
        m = re.search(
            r"average\s+core\s+funding\s+ratio[^\d]{0,60}([\d.]+)\s*%",
            text, re.IGNORECASE
        )
        if m:
            cfr_curr = float(m.group(1))

    # CET1 / leverage
    cet1_curr, cet1_prev = None, None
    m = re.search(
        r"(?:common\s+equity\s+tier\s+1|CET[- ]?1)[^\d]{0,80}([\d.]+)\s*%[^\d]{0,80}([\d.]+)\s*%",
        text, re.IGNORECASE
    )
    if m:
        cet1_curr = float(m.group(1))
        cet1_prev = float(m.group(2))

    lev_curr, lev_prev = None, None
    m = re.search(
        r"leverage\s+ratio[^\d]{0,60}([\d.]+)\s*%[^\d]{0,60}([\d.]+)\s*%",
        text, re.IGNORECASE
    )
    if m:
        lev_curr = float(m.group(1))
        lev_prev = float(m.group(2))

    # Description
    desc = ""
    for pat in [
        r"principal\s+activities?\s*\n(.*?)(?:\n\n|declaration)",
        r"the\s+(?:branch|company)\'s?\s+principal\s+activities?\s+are?\s+(.{60,500}?)\.",
        r"principal\s+activities?\s+(?:are|is|include)\s+(.{60,500}?)\.",
        r"the\s+(?:branch|company)\s+provides?\s+(.{60,400}?)\.",
    ]:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(raw) > 40:
                desc = raw[:480]
                break

    asset_bdown = extract_breakdown(text, ASSET_PATTERNS, unit_mult)
    liab_bdown = extract_breakdown(text, LIAB_PATTERNS, unit_mult)

    equity = None
    if total_assets_curr is not None and total_liab_curr is not None:
        equity = total_assets_curr - total_liab_curr
    elif total_assets_curr is not None:
        equity = 0.0

    missing = [k for k, v in [
        ("total_assets_curr", total_assets_curr),
        ("profit_curr", profit_curr),
    ] if v is None]
    if missing:
        st.warning(
            f"Could not extract: {', '.join(missing)}. "
            "This PDF may use a non-standard layout. Affected values will show as N/A."
        )

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
        spec_prov_curr=spec_curr, spec_prov_prev=spec_prev,
        coll_prov_curr=coll_curr, coll_prov_prev=coll_prev,
        provisions_curr=total_prov_curr, provisions_prev=total_prov_prev,
        lmr_curr=lmr_curr, lmr_prev=lmr_prev,
        cfr_curr=cfr_curr, cfr_prev=cfr_prev,
        cet1_curr=cet1_curr, cet1_prev=cet1_prev,
        lev_curr=lev_curr, lev_prev=lev_prev,
        equity=equity, asset_bdown=asset_bdown, liab_bdown=liab_bdown,
    )


# ── FORMATTING HELPERS ────────────────────────────────────────────────────────

def fmt(v, um):
    if v is None:
        return "N/A"
    n = v / um
    if abs(n) >= 1000:
        return f"{n:,.0f}"
    elif abs(n) >= 10:
        return f"{n:,.1f}"
    else:
        return f"{n:,.2f}"


def pct_chg(curr, prev):
    if curr is None or prev is None or prev == 0:
        return None
    return (curr - prev) / abs(prev) * 100


def pp_chg(curr, prev):
    if curr is None or prev is None:
        return None
    return curr - prev


def badge(val, positive_is_up=True):
    if val is None:
        return ""
    cls = "badge-up" if (val > 0) == positive_is_up else "badge-dn"
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:.1f}%</span>'


def pp_badge(val):
    if val is None:
        return ""
    cls = "badge-up" if val > 0 else "badge-dn"
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:.1f}pp</span>'


def na(v, um, cy, is_pct=False):
    if v is None:
        return "N/A"
    if is_pct:
        return f"{v:.2f}%"
    return f"{cy} {fmt(v, um)}"


# ── ANALYSIS ENGINE ───────────────────────────────────────────────────────────

def build_analysis(d):
    um = d["unit_mult"]
    cy = d["currency"]
    out = {}

    lmr_c = d["lmr_curr"]
    lmr_p = d["lmr_prev"]
    cfr_c = d["cfr_curr"]
    cfr_p = d["cfr_prev"]
    profit = d["profit_curr"]
    profit_p = d["profit_prev"]
    total_a = d["total_assets_curr"]
    total_a_p = d["total_assets_prev"]
    total_l = d["total_liab_curr"]
    loans = d["loans_curr"]
    deposits = d["deposits_curr"]
    equity = d["equity"]
    prov = d["provisions_curr"]
    prov_p = d["provisions_prev"]
    int_inc = d["int_income_curr"]
    spec = d["spec_prov_curr"]
    coll = d["coll_prov_curr"]
    ab = d["asset_bdown"] or {}
    lb = d["liab_bdown"] or {}

    # Derived
    roa = (profit / total_a * 100) if profit and total_a else None
    roe = (profit / equity * 100) if profit and equity and equity > 0 else None
    prov_change = pct_chg(prov, prov_p)
    profit_growth = pct_chg(profit, profit_p)
    asset_growth = pct_chg(total_a, total_a_p)
    ldr = (loans / deposits * 100) if loans and deposits else None
    lmr_diff = pp_chg(lmr_c, lmr_p)
    cfr_diff = pp_chg(cfr_c, cfr_p)

    # ── LMR narrative ──
    if lmr_c is not None:
        direction = "increased" if (lmr_diff or 0) > 0 else "decreased" if (lmr_diff or 0) < 0 else "remained stable"
        if lmr_c >= 300:
            level_desc = "exceptionally high"
        elif lmr_c >= 150:
            level_desc = "very strong"
        elif lmr_c >= 75:
            level_desc = "solid"
        elif lmr_c >= 35:
            level_desc = "adequate but lean"
        else:
            level_desc = "tight -- approaching the 25% regulatory floor"

        if lmr_c >= 150 and ab:
            top_a = max(ab, key=ab.get) if ab else ""
            if "Overseas" in top_a:
                reason = ("high intragroup asset placements that count as HQLA, "
                          "reflecting the branch's role as a group liquidity vehicle")
            else:
                reason = ("a structurally large stock of liquid assets relative to short-term liabilities, "
                          "consistent with conservative treasury positioning")
        else:
            reason = "normal balance sheet management within internal limits"

        if lmr_diff and abs(lmr_diff) > 20:
            likely_cause = (
                "a significant shift in the short-term funding mix -- either a reduction in wholesale "
                "borrowings (which shrinks the denominator) or an increase in liquid asset holdings. "
                "Executives should verify whether this is a deliberate positioning change or a temporary "
                "balance sheet fluctuation ahead of the reporting date."
            )
        elif lmr_diff and lmr_diff > 0:
            likely_cause = "modest accumulation of HQLA or a small reduction in short-term liabilities"
        elif lmr_diff and lmr_diff < 0:
            likely_cause = ("deployment of liquid assets into higher-yielding loans or interbank placements, "
                            "or an increase in short-term wholesale funding")
        else:
            likely_cause = "stable balance sheet composition with no material change in liquidity drivers"

        out["lmr_direction"] = direction
        out["lmr_level"] = level_desc
        out["lmr_reason"] = reason
        out["lmr_cause"] = likely_cause
        out["lmr_c"] = lmr_c
        out["lmr_p"] = lmr_p
        out["lmr_diff"] = lmr_diff
    else:
        out["lmr_direction"] = out["lmr_level"] = out["lmr_reason"] = out["lmr_cause"] = None
        out["lmr_c"] = out["lmr_p"] = out["lmr_diff"] = None

    # ── CFR narrative ──
    if cfr_c is not None:
        cfr_dir = "decreased" if (cfr_diff or 0) < 0 else "increased" if (cfr_diff or 0) > 0 else "remained stable"
        if cfr_c >= 200:
            cfr_meaning = (f"stable funding covers illiquid assets by {cfr_c/100:.1f}x, "
                           "providing strong structural resilience. The branch is not dependent "
                           "on short-term wholesale markets to fund its balance sheet.")
        elif cfr_c >= 100:
            cfr_meaning = ("stable funding just covers illiquid assets. The branch meets the "
                           "structural funding requirement but has limited buffer against deposit outflows.")
        else:
            cfr_meaning = ("stable funding does not fully cover illiquid assets -- a structural "
                           "maturity mismatch. The branch relies on short-term funding to finance "
                           "longer-term assets.")
        out["cfr_dir"] = cfr_dir
        out["cfr_meaning"] = cfr_meaning
        out["cfr_c"] = cfr_c
        out["cfr_p"] = cfr_p
        out["cfr_diff"] = cfr_diff
    else:
        out["cfr_dir"] = out["cfr_meaning"] = None
        out["cfr_c"] = out["cfr_p"] = out["cfr_diff"] = None

    # ── Asset concentration narrative ──
    if ab and total_a:
        sorted_a = sorted(ab.items(), key=lambda x: x[1], reverse=True)[:3]
        top_a_name = sorted_a[0][0] if sorted_a else ""
        if "Overseas" in top_a_name:
            asset_analysis = (
                f"The dominance of {top_a_name} ({sorted_a[0][1]/total_a*100:.1f}% of total assets) "
                "confirms this branch operates primarily as an intragroup booking and funding vehicle. "
                "Credit risk is concentrated at the parent group level. Local provisions are largely "
                "symbolic -- the real credit exposure is the parent's balance sheet, not local borrowers. "
                "The HKMA monitors this structure closely under its overseas branch supervisory framework."
            )
        elif "Loans" in top_a_name:
            llr = (prov / loans * 100) if prov and loans else None
            asset_analysis = (
                f"A loan-dominant balance sheet ({sorted_a[0][1]/total_a*100:.1f}%) means revenue is "
                "primarily spread-based and credit risk sits with local/external borrowers. "
                + (f"The loan loss reserve of {llr:.2f}% of gross loans " if llr else "")
                + ("is adequate." if llr and llr > 1 else "is thin -- watch for provision increases." if llr else "")
                + " The provisions trajectory is the primary forward-looking credit indicator."
            )
        else:
            asset_analysis = (
                "The diversified asset mix means no single risk driver dominates. "
                "Revenue and credit risk are distributed across business lines."
            )
        out["asset_analysis"] = asset_analysis
        out["top_assets_curr"] = sorted_a
        out["top_assets_pct"] = [(n, v/total_a*100) for n, v in sorted_a]
    else:
        out["asset_analysis"] = None
        out["top_assets_curr"] = out["top_assets_pct"] = None

    # ── Liability concentration narrative ──
    if lb and total_l:
        sorted_l = sorted(lb.items(), key=lambda x: x[1], reverse=True)[:3]
        top_l_name = sorted_l[0][0] if sorted_l else ""
        if "Customer" in top_l_name:
            liab_analysis = (
                f"Customer deposits ({sorted_l[0][1]/total_l*100:.1f}% of liabilities) are the primary "
                "funding source -- stable but subject to repricing and behavioural run risk under stress. "
                + (f"With an LMR of {lmr_c:.1f}%, the branch holds sufficient HQLA to absorb a 30-day withdrawal scenario." if lmr_c else "")
            )
        elif "Overseas" in top_l_name or "Interbank" in top_l_name:
            liab_analysis = (
                f"Wholesale and intragroup funding ({sorted_l[0][1]/total_l*100:.1f}%) dominates. "
                "This is the most fragile funding source -- it can be withdrawn overnight. "
                "Any stress at parent level transmits directly to this balance sheet."
            )
        else:
            liab_analysis = (
                "The funding base is diversified. No single source creates a dominant concentration risk, "
                "though the maturity profile and repricing terms should be reviewed in the liquidity notes."
            )
        out["liab_analysis"] = liab_analysis
        out["top_liabs_curr"] = sorted_l
        out["top_liabs_pct"] = [(n, v/total_l*100) for n, v in sorted_l]
    else:
        out["liab_analysis"] = None
        out["top_liabs_curr"] = out["top_liabs_pct"] = None

    # ── Credit risk sentence ──
    if prov is not None:
        direction = "rose" if (prov_change or 0) > 0 else "fell"
        pct_abs = abs(prov_change) if prov_change else 0

        if spec and coll:
            prov_driver = "a mix of specific and collective provisions"
            prov_impl = ("both identified borrower deterioration and broader portfolio-level stress" if (prov_change or 0) > 0
                         else "releases across both specific impaired credits and collective model updates")
        elif spec:
            prov_driver = "specific provisions"
            prov_impl = ("more identified credit risk on named counterparties" if (prov_change or 0) > 0
                         else "less identified credit risk -- specific provisions released")
        elif coll:
            prov_driver = "collective provisions"
            prov_impl = ("a broader portfolio-level stress signal" if (prov_change or 0) > 0
                         else "improving expected loss estimates across the portfolio")
        else:
            prov_driver = "provisions"
            prov_impl = ("more identified credit risk" if (prov_change or 0) > 0 else "improving credit quality")

        top_a_name = ""
        if ab and total_a:
            top_a_name = max(ab, key=ab.get)

        if "Overseas" in top_a_name:
            credit_loc = "the parent group and its global counterparties"
            credit_ctx = ("Local provisions are largely symbolic in this context -- the real credit "
                          "exposure is the consolidated group balance sheet.")
        elif "Loans" in top_a_name:
            credit_loc = "external borrowers in the local loan book"
            credit_ctx = ("The provisions trajectory is the key leading indicator -- it typically "
                          "leads NPL recognition by one to two quarters.")
        else:
            credit_loc = "a mix of local and intragroup counterparties"
            credit_ctx = "Credit risk is distributed; no single exposure is likely to be systemic."

        if prov_change is not None:
            out["credit_sentence"] = (
                f"Provisions {direction} {pct_abs:.1f}%, driven by {prov_driver}, "
                f"implying {prov_impl}. "
                f"The dominant asset is {top_a_name if top_a_name else 'not identifiable from this filing'}, "
                f"so credit risk sits primarily with {credit_loc}. {credit_ctx}"
            )
        else:
            out["credit_sentence"] = (
                f"Provisions are reported but no prior-period comparison is available. "
                f"The dominant asset suggests credit risk sits with {credit_loc}. {credit_ctx}"
            )
    else:
        out["credit_sentence"] = None

    # ── Overall summary ──
    positives = []
    negatives = []
    if lmr_c and lmr_c >= 100:
        positives.append(f"strong short-term liquidity (LMR {lmr_c:.1f}%)")
    if cfr_c and cfr_c >= 200:
        positives.append(f"structurally sound funding (CFR {cfr_c:.1f}%)")
    if roa and roa > 0.5:
        positives.append(f"above-average profitability (ROA {roa:.2f}%)")
    if profit_growth and profit_growth > 10:
        positives.append(f"strong earnings growth ({profit_growth:.1f}%)")
    if lmr_c and lmr_c < 50:
        negatives.append(f"lean liquidity buffer (LMR {lmr_c:.1f}%)")
    if cfr_c and cfr_c < 100:
        negatives.append("structural funding shortfall (CFR below 100%)")
    if profit and profit < 0:
        negatives.append("loss-making in current period")
    if profit_growth and profit_growth < -20:
        negatives.append(f"severe profit decline ({profit_growth:.1f}%)")
    if prov_change and prov_change > 30:
        negatives.append(f"sharply rising provisions (+{prov_change:.1f}%)")

    entity = d.get("entity", "This institution")
    if positives and not negatives:
        verdict_tone = "presents a fundamentally sound profile."
    elif positives and negatives:
        verdict_tone = "has clear strengths alongside areas requiring attention."
    elif negatives:
        verdict_tone = "shows multiple indicators that require executive attention."
    else:
        verdict_tone = "presents a mixed picture requiring further investigation."

    verdict = f"{entity} {verdict_tone}"
    if positives:
        verdict += f" Strengths: {'; '.join(positives)}."
    if negatives:
        verdict += f" Concerns: {'; '.join(negatives)}."

    if lmr_c and cfr_c and (profit or 0) > 0:
        if lmr_c >= 100 and cfr_c >= 100:
            verdict += (" The combination of strong liquidity, adequate structural funding, and positive "
                        "profitability is the hallmark of a well-managed branch. "
                        "Primary risk vectors are external: rate cycle shifts, parent group credit events, "
                        "or macro shocks to the HK interbank market.")

    out["verdict"] = verdict
    out["roa"] = roa
    out["roe"] = roe
    out["profit_growth"] = profit_growth
    out["asset_growth"] = asset_growth
    return out


# ── RENDER ────────────────────────────────────────────────────────────────────

def render_bar(breakdown, total, title):
    if not breakdown or not total:
        st.markdown(
            '<div class="neutral-box">Breakdown not available for this filing.</div>',
            unsafe_allow_html=True
        )
        return
    items = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, v in items]
    values = [v / total * 100 for k, v in items]
    SG = ["#E60028", "#1A1A1A", "#6B6B6B", "#BFBFBF", "#D9D9D9", "#F0F0F0"]
    fig, ax = plt.subplots(figsize=(4.6, max(2.4, len(labels) * 0.45)))
    bars = ax.barh([l[:32] for l in labels], values,
                   color=SG[:len(labels)], edgecolor="none", height=0.55)
    ax.set_xlabel("% of Total", fontsize=7.5, color="#6B6B6B")
    ax.set_title(title, fontsize=9, fontweight="bold", color="#1A1A1A", pad=8)
    ax.tick_params(axis="y", labelsize=7.5, colors="#1A1A1A")
    ax.tick_params(axis="x", labelsize=7, colors="#6B6B6B")
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#D9D9D9")
    ax.set_facecolor("#FFFFFF")
    fig.patch.set_facecolor("#FFFFFF")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", ha="left", fontsize=7, color="#1A1A1A")
    ax.set_xlim(0, max(values) * 1.3)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_report(d):
    um = d["unit_mult"]
    cy = d["currency"]
    ana = build_analysis(d)

    # ── ENTITY HEADER ──
    st.markdown(f"""
    <div class="entity-header">
      <h2>{d["entity"]}</h2>
      <div class="meta">Period: {d["report_date"]} &nbsp;|&nbsp; Figures in {cy} {d["unit_label"]}</div>
    </div>""", unsafe_allow_html=True)

    if d["description"]:
        st.markdown(
            f'<div class="info-box"><strong>Principal activities:</strong> {d["description"]}</div>',
            unsafe_allow_html=True
        )

    # ── OVERALL TAKEAWAY ──
    st.markdown('<div class="section-header">Main Takeaway</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="analysis-box"><p>{ana["verdict"]}</p></div>',
        unsafe_allow_html=True
    )

    # ── KPI CARDS ──
    st.markdown('<div class="section-header">Key Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    def kpi(col, label, curr, prev, is_pct=False):
        with col:
            if is_pct:
                val_str = f"{curr:.2f}%" if curr is not None else "N/A"
                diff = pp_chg(curr, prev)
                b = pp_badge(diff) if diff is not None else ""
            else:
                val_str = f"{cy} {fmt(curr, um)}" if curr is not None else "N/A"
                chg = pct_chg(curr, prev)
                b = badge(chg) if chg is not None else ""
            st.markdown(f"""<div class="card">
              <div class="card-title">{label}</div>
              <div class="card-value">{val_str}{b}</div>
              <div class="card-sub">vs prior period</div>
            </div>""", unsafe_allow_html=True)

    kpi(c1, "Total Assets", d["total_assets_curr"], d["total_assets_prev"])
    kpi(c2, "Net Profit / (Loss)", d["profit_curr"], d["profit_prev"])
    kpi(c3, "Avg LMR", d["lmr_curr"], d["lmr_prev"], is_pct=True)
    kpi(c4, "Avg CFR", d["cfr_curr"], d["cfr_prev"], is_pct=True)

    # ── LIQUIDITY ──
    st.markdown('<div class="section-header">Liquidity Ratios</div>', unsafe_allow_html=True)

    if ana["lmr_c"] is not None:
        lmr_p_str = f"{ana['lmr_p']:.2f}% (prior)" if ana["lmr_p"] else "N/A (prior)"
        lmr_diff_str = f"{ana['lmr_diff']:+.2f}pp" if ana["lmr_diff"] is not None else "N/A"
        lmr_block = f"""
        <div class="analysis-box">
          <h3>3-Month Avg Liquidity Maintenance Ratio (LMR)</h3>
          <p><strong>{ana["lmr_c"]:.2f}%</strong> (current) &nbsp; | &nbsp;
             <strong>{lmr_p_str}</strong> &nbsp; | &nbsp;
             Change: <strong>{lmr_diff_str}</strong></p>
          <p>The LMR {ana["lmr_direction"]} from {lmr_p_str.replace(" (prior)","")} to {ana["lmr_c"]:.2f}%.</p>
          <p>{d["entity"]} holds enough liquid assets to cover approximately {ana["lmr_c"]:.0f}% of liabilities due within one month.</p>
          <p>Reason for change: {ana["lmr_reason"]}.</p>
          <p>Most likely caused by: {ana["lmr_cause"]}</p>
          <p>The LMR remains {"well above" if (ana["lmr_c"] or 0) > 50 else "above"} the 25% regulatory minimum.</p>
        </div>"""
        st.markdown(lmr_block, unsafe_allow_html=True)

    if ana["cfr_c"] is not None:
        cfr_p_str = f"{ana['cfr_p']:.2f}%" if ana["cfr_p"] else "N/A"
        cfr_diff_str = f"{ana['cfr_diff']:+.2f}pp" if ana["cfr_diff"] is not None else "N/A"
        cfr_block = f"""
        <div class="analysis-box">
          <h3>3-Month Avg Core Funding Ratio (CFR)</h3>
          <p><strong>{ana["cfr_c"]:.2f}%</strong> (current) &nbsp; | &nbsp;
             <strong>{cfr_p_str} (prior)</strong> &nbsp; | &nbsp;
             Change: <strong>{cfr_diff_str}</strong></p>
          <p>The CFR {ana["cfr_dir"]}, going from {cfr_p_str} to {ana["cfr_c"]:.2f}%.</p>
          <p>This means: {ana["cfr_meaning"]}</p>
          <p>CFR remains {"well above" if (ana["cfr_c"] or 0) > 100 else "above"} the 75% regulatory minimum.</p>
        </div>"""
        st.markdown(cfr_block, unsafe_allow_html=True)

    if ana["lmr_c"] and ana["cfr_c"]:
        lmr_lvl = ana["lmr_c"]
        cfr_lvl = ana["cfr_c"]
        if lmr_lvl > 50 and cfr_lvl > 100:
            liq_summary = (f"In terms of liquidity, {d['entity']} is above average on both ratios "
                           f"and is able to cover over {lmr_lvl:.0f}% of its one-month liabilities.")
        else:
            liq_summary = (f"Liquidity ratios are within regulatory bounds. "
                           f"LMR of {lmr_lvl:.1f}% and CFR of {cfr_lvl:.1f}% indicate "
                           f"adequate but not exceptional liquidity positioning.")
        st.markdown(f'<div class="neutral-box">{liq_summary}</div>', unsafe_allow_html=True)

    # ── FINANCIAL SUMMARY TABLE ──
    st.markdown('<div class="section-header">Financial Summary</div>', unsafe_allow_html=True)

    def trow(label, curr, prev, bold=False, is_pct=False):
        if is_pct:
            c_s = f"{curr:.2f}%" if curr is not None else "N/A"
            p_s = f"{prev:.2f}%" if prev is not None else "N/A"
            diff = pp_chg(curr, prev)
            d_s = (f"{diff:+.2f}pp" if diff is not None else "N/A")
        else:
            c_s = na(curr, um, cy)
            p_s = na(prev, um, cy)
            chg = pct_chg(curr, prev)
            d_s = (f"{chg:+.1f}%" if chg is not None else "N/A")
        cls = 'bold-row' if bold else ''
        return (f'<tr class="{cls}"><td>{label}</td>' +
                f'<td class="num">{c_s}</td><td class="num">{p_s}</td>' +
                f'<td class="num">{d_s}</td></tr>')

    rows = ""
    rows += trow("Interest Income", d["int_income_curr"], d["int_income_prev"])
    rows += trow("Total Operating Income", d["op_income_curr"], d["op_income_prev"])
    rows += trow("Profit after Taxation", d["profit_curr"], d["profit_prev"], bold=True)
    rows += trow("Total Assets", d["total_assets_curr"], d["total_assets_prev"], bold=True)
    rows += trow("Total Liabilities", d["total_liab_curr"], d["total_liab_prev"])
    rows += trow("Specific Provisions", d["spec_prov_curr"], d["spec_prov_prev"])
    rows += trow("Collective Provisions", d["coll_prov_curr"], d["coll_prov_prev"])
    rows += trow("Total Provisions", d["provisions_curr"], d["provisions_prev"], bold=True)

    st.markdown(f"""<table class="styled">
      <thead><tr>
        <th style="width:36%">Item</th>
        <th class="num" style="width:20%">'25</th>
        <th class="num" style="width:20%">'24</th>
        <th class="num" style="width:24%">Change</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

    # ── REGULATORY RATIOS ──
    st.markdown('<div class="section-header">Regulatory Ratios</div>', unsafe_allow_html=True)
    r_rows = ""
    r_rows += trow("Avg LMR", d["lmr_curr"], d["lmr_prev"], is_pct=True)
    r_rows += trow("Avg CFR", d["cfr_curr"], d["cfr_prev"], is_pct=True)
    r_rows += trow("CET1 Ratio", d["cet1_curr"], d["cet1_prev"], is_pct=True)
    r_rows += trow("Leverage Ratio", d["lev_curr"], d["lev_prev"], is_pct=True)
    st.markdown(f"""<table class="styled">
      <thead><tr>
        <th style="width:36%">Ratio</th>
        <th class="num" style="width:20%">Current</th>
        <th class="num" style="width:20%">Prior</th>
        <th class="num" style="width:24%">Change</th>
      </tr></thead>
      <tbody>{r_rows}</tbody>
    </table>""", unsafe_allow_html=True)

    # ── BALANCE SHEET COMPOSITION ──
    st.markdown('<div class="section-header">Balance Sheet Composition</div>', unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)
    with ch1:
        render_bar(d["asset_bdown"], d["total_assets_curr"], "Asset Composition")
    with ch2:
        render_bar(d["liab_bdown"], d["total_liab_curr"], "Liability Composition")

    # ── ASSET CONCENTRATION ──
    st.markdown('<div class="section-header">Asset Concentration</div>', unsafe_allow_html=True)

    def render_conc_table(items_pct, total, um, cy, date_label):
        if not items_pct:
            st.markdown('<div class="neutral-box">Not extractable from this filing.</div>', unsafe_allow_html=True)
            return
        rows_html = ""
        for i, (name, pct) in enumerate(items_pct, 1):
            val = total * pct / 100 if total else None
            val_str = f"{cy} {fmt(val, um)}" if val else "N/A"
            rows_html += f"""<div class="conc-item">
              <span class="conc-rank">{i}</span>
              <span class="conc-name">{name}</span>
              <span class="conc-pct">{pct:.1f}%</span>
              <span class="conc-val">{val_str}</span>
            </div>"""
        st.markdown(f'<div style="background:#fff;border-top:2px solid #E60028;padding:14px 18px;margin-bottom:10px;">' +
                    f'<div style="font-size:0.66rem;font-weight:700;color:#6B6B6B;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:8px;">{date_label}</div>' +
                    rows_html + '</div>', unsafe_allow_html=True)

    if ana["top_assets_pct"]:
        render_conc_table(ana["top_assets_pct"], d["total_assets_curr"], um, cy, f"Current Period -- {d['report_date']}")

    if ana.get("asset_analysis"):
        st.markdown(
            f'<div class="analysis-box"><h3>Analysis</h3><p>{ana["asset_analysis"]}</p></div>',
            unsafe_allow_html=True
        )

    # ── LIABILITY CONCENTRATION ──
    st.markdown('<div class="section-header">Liability Concentration</div>', unsafe_allow_html=True)

    if ana["top_liabs_pct"]:
        render_conc_table(ana["top_liabs_pct"], d["total_liab_curr"], um, cy, f"Current Period -- {d['report_date']}")

    if ana.get("liab_analysis"):
        st.markdown(
            f'<div class="analysis-box"><h3>Analysis</h3><p>{ana["liab_analysis"]}</p></div>',
            unsafe_allow_html=True
        )

    # ── CREDIT RISK ──
    st.markdown('<div class="section-header">Asset Quality and Credit Risk</div>', unsafe_allow_html=True)
    if ana.get("credit_sentence"):
        st.markdown(
            f'<div class="analysis-box"><h3>Credit Risk Assessment</h3><p>{ana["credit_sentence"]}</p></div>',
            unsafe_allow_html=True
        )

    # ── EXECUTIVE ANALYSIS ──
    st.markdown('<div class="section-header">Executive Analysis -- Key Takeaways</div>', unsafe_allow_html=True)

    exec_content = ""
    if ana.get("lmr_c") is not None and ana.get("cfr_c") is not None:
        exec_content += (
            f"<p><strong>Liquidity:</strong> "
            f"LMR of {ana['lmr_c']:.1f}% ({ana['lmr_level']}) and CFR of {ana['cfr_c']:.1f}% "
            f"indicate the branch is {"well-positioned" if ana['lmr_c'] > 50 and ana['cfr_c'] > 100 else "adequately positioned"} "
            f"on both short-term and structural liquidity. "
            f"The LMR {ana['lmr_direction']} primarily due to {ana['lmr_reason']}. "
            f"Structurally, {ana['cfr_meaning']}</p>"
        )

    if ana.get("asset_analysis"):
        exec_content += f"<p><strong>Balance Sheet Composition:</strong> {ana['asset_analysis']}</p>"

    if ana.get("credit_sentence"):
        exec_content += f"<p><strong>Credit Risk:</strong> {ana['credit_sentence']}</p>"

    if ana.get("profit_growth") is not None:
        pg = ana["profit_growth"]
        if abs(pg) > 50:
            pg_note = f"Profit {'surged' if pg > 0 else 'collapsed'} {abs(pg):.0f}% -- verify whether driven by operating leverage, provision releases, or one-off items."
        elif abs(pg) > 15:
            pg_note = f"Profit {'grew' if pg > 0 else 'fell'} {abs(pg):.0f}%, a {'solid' if pg > 0 else 'significant'} move. Monitor the provisions trend as the leading credit quality indicator."
        else:
            pg_note = f"Profit is broadly stable ({pg:+.1f}%). Earnings quality depends on the provisions trajectory and revenue mix."
        exec_content += f"<p><strong>Profitability:</strong> {pg_note}</p>"

    exec_content += f"<p><strong>Bottom Line:</strong> {ana['verdict']}</p>"

    st.markdown(
        f'<div class="analysis-box">{exec_content}</div>',
        unsafe_allow_html=True
    )

    # ── CSV DOWNLOAD ──
    st.markdown('<div class="section-header">Export</div>', unsafe_allow_html=True)
    import csv, io as _io
    buf = _io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Metric", "Current", "Prior", "Change"])
    for label, curr, prev in [
        ("Total Assets", d["total_assets_curr"], d["total_assets_prev"]),
        ("Total Liabilities", d["total_liab_curr"], d["total_liab_prev"]),
        ("Interest Income", d["int_income_curr"], d["int_income_prev"]),
        ("Operating Income", d["op_income_curr"], d["op_income_prev"]),
        ("Profit after Tax", d["profit_curr"], d["profit_prev"]),
        ("Loans & Receivables", d["loans_curr"], d["loans_prev"]),
        ("Customer Deposits", d["deposits_curr"], d["deposits_prev"]),
        ("Specific Provisions", d["spec_prov_curr"], d["spec_prov_prev"]),
        ("Collective Provisions", d["coll_prov_curr"], d["coll_prov_prev"]),
        ("Total Provisions", d["provisions_curr"], d["provisions_prev"]),
        ("LMR (%)", d["lmr_curr"], d["lmr_prev"]),
        ("CFR (%)", d["cfr_curr"], d["cfr_prev"]),
    ]:
        chg = pct_chg(curr, prev)
        w.writerow([label,
                    fmt(curr, um) if curr is not None else "N/A",
                    fmt(prev, um) if prev is not None else "N/A",
                    f"{chg:+.1f}%" if chg is not None else "N/A"])
    st.download_button(
        "Download CSV",
        data=buf.getvalue(),
        file_name=f"{d['entity'].replace(' ', '_')}_{d['report_date'].replace(' ', '_')}.csv",
        mime="text/csv"
    )


# ── MAIN ──────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload HKMA Banking Disclosure PDF",
    type=["pdf"],
    help="Supports all standard HKMA Banking (Disclosure) Rules filings"
)

if uploaded:
    with st.spinner("Reading PDF..."):
        text = extract_text(uploaded)
    with st.spinner("Extracting and analysing data..."):
        data = extract_all(text)
    render_report(data)
else:
    st.markdown('<div class="neutral-box">Upload a PDF above to generate an analysis.</div>', unsafe_allow_html=True)
