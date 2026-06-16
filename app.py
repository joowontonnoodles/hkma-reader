import streamlit as st
import pdfplumber
import pandas as pd
import re, io

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# CSS — White / Black / Red / Gray only. DM Sans font (closest free to Asta Sans).
# ZERO black backgrounds.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ─ global reset ─ */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
.main, .block-container,
[data-testid="stVerticalBlock"],
[class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #ffffff !important;
    color: #111111 !important;
}

.block-container {
    max-width: 860px !important;
    padding: 2.5rem 2rem 5rem !important;
}

/* ─ headings ─ */
h1 {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #E60028 !important;
    border-bottom: 1.5px solid #E60028 !important;
    padding-bottom: 10px !important;
    margin-bottom: 4px !important;
}
h2 {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #555555 !important;
    border-bottom: 1px solid #e8e8e8 !important;
    padding-bottom: 5px !important;
    margin-top: 36px !important;
    margin-bottom: 10px !important;
}
h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.63rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #888888 !important;
    margin-top: 22px !important;
    margin-bottom: 8px !important;
}
p, span, div, li { color: #111111 !important; }

/* ─ page header ─ */
.pg-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 2px solid #111111;
    padding-bottom: 12px;
    margin-bottom: 4px;
}
.pg-bank {
    font-size: 1.45rem;
    font-weight: 700;
    color: #111111 !important;
    letter-spacing: -0.01em;
    line-height: 1;
}
.pg-bank span { color: #E60028 !important; }
.pg-meta {
    font-size: 0.68rem;
    color: #999999 !important;
    text-align: right;
    line-height: 1.7;
}
.unit-tag {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #E60028 !important;
    border: 1px solid #E60028;
    padding: 2px 8px;
    margin: 10px 0 20px 0;
}

/* ─ description block ─ */
.desc-block {
    border-left: 3px solid #E60028;
    padding: 10px 14px;
    background: #f9f9f9 !important;
    margin-bottom: 28px;
}
.desc-text {
    font-size: 0.78rem;
    color: #444444 !important;
    line-height: 1.65;
}

/* ─ snapshot KPI strip ─ */
.snapshot {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1px;
    background: #e8e8e8;
    border: 1px solid #e8e8e8;
    margin-bottom: 32px;
}
.kpi {
    background: #ffffff !important;
    padding: 14px 16px;
}
.kpi-label {
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #999999 !important;
    margin-bottom: 6px;
}
.kpi-val {
    font-size: 1.05rem;
    font-weight: 700;
    color: #111111 !important;
    line-height: 1;
}
.kpi-chg-pos {
    font-size: 0.65rem;
    color: #1a7a3a !important;
    margin-top: 4px;
}
.kpi-chg-neg {
    font-size: 0.65rem;
    color: #E60028 !important;
    margin-top: 4px;
}
.kpi-unit {
    font-size: 0.58rem;
    color: #bbbbbb !important;
    margin-top: 2px;
}

/* ─ ratio cards ─ */
.ratio-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 12px 0 28px;
}
.ratio-card {
    border: 1px solid #e8e8e8;
    border-top: 2.5px solid #E60028;
    padding: 16px 18px;
    background: #ffffff !important;
}
.ratio-label {
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #aaaaaa !important;
    margin-bottom: 10px;
}
.ratio-main {
    font-size: 1.6rem;
    font-weight: 700;
    color: #111111 !important;
    line-height: 1;
}
.ratio-prior { font-size: 0.72rem; color: #cccccc !important; margin-left: 6px; }
.chg-pos { font-size: 0.68rem; font-weight: 600; color: #1a7a3a !important; }
.chg-neg { font-size: 0.68rem; font-weight: 600; color: #E60028 !important; }

/* ─ tables ─ */
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.77rem;
    margin: 6px 0 20px;
    background: #ffffff !important;
}
thead tr { border-bottom: 2px solid #111111; }
th {
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #999999 !important;
    background: #ffffff !important;
    padding: 0 12px 8px;
    text-align: right;
    white-space: nowrap;
}
th:first-child { text-align: left; }
td {
    padding: 8px 12px;
    border-bottom: 1px solid #f2f2f2;
    color: #222222 !important;
    text-align: right;
    background: #ffffff !important;
}
td:first-child { text-align: left; font-weight: 500; color: #111111 !important; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fef5f5 !important; }
.pos { color: #1a7a3a !important; font-weight: 600; }
.neg { color: #E60028 !important; font-weight: 600; }
.muted { color: #bbbbbb !important; }

/* ─ rank badge ─ */
.rank {
    display: inline-block;
    width: 18px; height: 18px;
    line-height: 18px;
    text-align: center;
    font-size: 0.6rem;
    font-weight: 700;
    color: #E60028 !important;
    border: 1px solid #E60028;
    margin-right: 8px;
    vertical-align: middle;
}

/* ─ divider ─ */
.rule { border: none; border-top: 1px solid #e8e8e8; margin: 32px 0 0; }

/* ─ upload area ─ */
[data-testid="stFileUploader"] {
    border: 1px dashed #dddddd !important;
    background: #fafafa !important;
    padding: 6px !important;
}

/* ─ download button ─ */
[data-testid="stDownloadButton"] > button {
    background: #ffffff !important;
    border: 1.5px solid #111111 !important;
    color: #111111 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 8px 20px !important;
    border-radius: 0 !important;
    transition: all 0.15s;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #E60028 !important;
    border-color: #E60028 !important;
    color: #ffffff !important;
}

/* ─ expander ─ */
[data-testid="stExpander"] {
    border: 1px solid #eeeeee !important;
    background: #fafafa !important;
}
details summary { color: #cccccc !important; font-size: 0.68rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL LABELS
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL = {
    r"cash and balances":                                           "Cash and balances with banks",
    r"balances due from exchange fund|due from exchange fund":      "Due from Exchange Fund",
    r"placements with banks":                                       "Placements with banks",
    r"amounts? due from overseas offices|due from overseas offices":"Amounts due from overseas offices",
    r"trade bills":                                                 "Trade bills",
    r"certificates? of deposit held":                              "Certificates of deposit held",
    r"securities held for trading":                                 "Securities held for trading",
    r"advances and other accounts":                                 "Advances and other accounts",
    r"loans and receivables":                                       "Loans and receivables",
    r"investment securities":                                       "Investment securities",
    r"other investments":                                           "Other investments",
    r"property.*plant.*equipment":                                  "Property, plant & equipment",
    r"deposits and balances from banks":                            "Deposits and balances from banks",
    r"balances due to exchange fund":                               "Balances due to Exchange Fund",
    r"demand deposits and current accounts|demand deposits":        "Demand deposits and current accounts",
    r"saving deposits":                                             "Saving deposits",
    r"time.*call.*notice deposits":                                 "Time, call and notice deposits",
    r"amounts? due to overseas offices":                            "Amount due to overseas offices",
    r"certificates? of deposit issued":                             "Certificates of deposit issued",
    r"issued debt securities":                                      "Issued debt securities",
    r"amount payable under repo":                                   "Amount payable under repo",
    r"other accounts and provisions|other liabilities":             "Other accounts / liabilities",
    r"^provisions$":                                                "Provisions",
    r"deposits from customers":                                     "Deposits from customers",
}

def canonicalize(raw):
    ll = raw.lower().strip()
    for pat, clean in CANONICAL.items():
        if re.search(pat, ll, re.IGNORECASE):
            return clean
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ", raw)
    s = re.sub(r"\s+"," ", s).strip()
    s = re.sub(r"[,\.\-\s]+$","", s).strip()
    return s[:70].rsplit(" ",1)[0].strip() if len(s)>70 else s

# ─────────────────────────────────────────────────────────────────────────────
# CORE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def clean_num(s):
    if not isinstance(s,str): return None
    s = s.strip().replace(",","").replace("\xa0","").replace(" ","")
    s = re.sub(r"HK\$|US\$|'000|港幣千元","",s).strip()
    if s in ("","—","-","–","Nil","nil","N/A"): return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[()$]","",s)
    try: v=float(s); return -v if neg else v
    except: return None

def trailing_nums(line):
    tokens = re.findall(r"\([\d,]+(?:\.\d+)?\)|[\d,]+(?:\.\d+)?", line)
    return [v for t in tokens for v in [clean_num(t)] if v is not None]

def raw_label(line):
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ", line)
    s = re.sub(r"(\s+[\(\-]?[\d,]+[\)]?)+\s*$","", s).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]{3,}.*$","", s)
    s = re.sub(r"\(see\s+part.*$","", s, flags=re.IGNORECASE).strip()
    s = re.sub(r",?\s*net\s+of\s+impairment\s+allowance","", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ", s)
    return re.sub(r"\s+"," ", s).strip()

def detect_unit(text):
    """Returns ('millions', 1_000_000) or ('thousands', 1_000)."""
    if re.search(r"in millions|millions of hk|million[s]? of hong kong", text, re.IGNORECASE):
        return "HKD millions", 1_000_000
    if re.search(r"HK\$\s*'?\s*0{3}", text, re.IGNORECASE):
        return "HKD thousands", 1_000
    if re.search(r"'000|thousands", text, re.IGNORECASE):
        return "HKD thousands", 1_000
    return "HKD thousands", 1_000   # safe default

def fmt_snapshot(v, multiplier):
    """Convert raw doc value → actual HKD → human-readable B/M."""
    if v is None: return "—"
    hkd = abs(v) * multiplier
    if hkd >= 1_000_000_000_000: return f"{hkd/1_000_000_000_000:.2f}T"
    if hkd >= 1_000_000_000:     return f"{hkd/1_000_000_000:.1f}B"
    if hkd >= 1_000_000:         return f"{hkd/1_000_000:.0f}M"
    return f"{hkd:,.0f}"

def fmt_n(v):
    if v is None: return "—"
    return f"{abs(v):,.0f}"

def pct_chg(c, p):
    if c is None or p is None or p == 0: return None
    return round((c-p)/abs(p)*100, 2)

def fmt_chg(v):
    if v is None: return '<span class="muted">—</span>'
    sign = "+" if v>0 else ""
    css  = "pos" if v>0 else "neg"
    return f'<span class="{css}">{sign}{v:.2f}%</span>'

def pp_html(v):
    if v is None: return '<span class="muted">—</span>'
    sign = "+" if v>0 else ""
    css  = "chg-pos" if v>0 else "chg-neg"
    return f'<span class="{css}">{sign}{v:.2f}pp</span>'

def is_noise(line):
    s = line.strip()
    if not s or len(s)<4: return True
    if re.match(r"^[^a-zA-Z0-9\-\(]", s): return True
    if re.match(r"^[A-Z]\d+\s*$", s): return True
    return False

def extract_pages(pdf_bytes):
    pages=[]
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i,page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            rows=[]
            for tbl in (page.extract_tables() or []):
                for row in tbl:
                    rows.append([c.strip() if isinstance(c,str) else (c or "") for c in row])
            pages.append((i, lines, rows))
    return pages

def ocr_all(pdf_bytes):
    if not OCR_AVAILABLE: return []
    imgs = convert_from_bytes(pdf_bytes, dpi=200)
    out=[]
    for img in imgs:
        t = pytesseract.image_to_string(img)
        out += [l.strip() for l in t.splitlines() if l.strip()]
    return out

# ─────────────────────────────────────────────────────────────────────────────
# BALANCE SHEET PARSER
# ─────────────────────────────────────────────────────────────────────────────
HARD_SKIP = re.compile(
    r"^total\s+(assets|liabilities)|^assets\s*$|^liabilities\s*$|"
    r"^less:\s*impairment|^impairment\s+allowances\s+for|^provision\s+for\s+impaired|"
    r"^balance\s+sheet|^section\s+[a-z]|^\d+\s*$|^page\s",
    re.IGNORECASE)
INCOME_SKIP = re.compile(
    r"profit\s+before\s+tax|profit\s+after\s+tax|interest\s+income|interest\s+expense|"
    r"operating\s+income|operating\s+expense|taxation\s+charge|tax\s+expense|"
    r"reversal\s+of\s+impairment|net\s+write\s+(back|charge)", re.IGNORECASE)
DED_SKIP = re.compile(r"^\s*-\s+(collective|specific)\b", re.IGNORECASE)

def parse_bs(lines, section="assets"):
    items=[]
    in_sec=False
    s_pat = re.compile(r"^assets\s*$|^assets\s+as\s+at", re.IGNORECASE) if section=="assets" \
            else re.compile(r"^liabilities\s*$", re.IGNORECASE)
    e_pat = re.compile(r"total\s+assets", re.IGNORECASE) if section=="assets" \
            else re.compile(r"total\s+liabilities", re.IGNORECASE)
    for line in lines:
        s=line.strip()
        if not s: continue
        if s_pat.match(s): in_sec=True; continue
        if not in_sec: continue
        if e_pat.search(s): in_sec=False; continue
        if HARD_SKIP.search(s) or INCOME_SKIP.search(s) or DED_SKIP.match(s): continue
        if is_noise(s): continue
        nums = trailing_nums(s)
        if not nums: continue
        curr  = nums[-2] if len(nums)>=2 else nums[-1]
        prior = nums[-1] if len(nums)>=2 else None
        if curr==0 and (prior is None or prior==0): continue
        rl    = raw_label(s)
        label = canonicalize(rl)
        if not label or len(label)<2: continue
        if re.match(r"^[\d,.()\-\s]+$", label): continue
        if any(x["label"]==label for x in items): continue
        items.append({"label":label,"curr":abs(curr),"prior":abs(prior) if prior is not None else None})
    return items

# ─────────────────────────────────────────────────────────────────────────────
# TARGETED FINDERS
# ─────────────────────────────────────────────────────────────────────────────
def find_two(lines, pattern):
    for i,line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            nums = trailing_nums(line)
            if len(nums)>=2: return nums[-2], nums[-1]
            for j in range(i+1, min(i+4, len(lines))):
                nums += trailing_nums(lines[j])
                if len(nums)>=2: return nums[-2], nums[-1]
    return None

def get_provisions(lines):
    spec, coll = None, None
    for line in lines:
        ll = line.lower()
        if re.search(r"collective\s+provision|[-–]\s*collective\b", ll):
            nums = trailing_nums(line)
            if nums and coll is None:
                coll = (abs(nums[-2] if len(nums)>=2 else nums[-1]),
                        abs(nums[-1]) if len(nums)>=2 else None)
        if re.search(r"specific\s+provision|[-–]\s*specific\b", ll):
            nums = trailing_nums(line)
            if nums and spec is None:
                spec = (abs(nums[-2] if len(nums)>=2 else nums[-1]),
                        abs(nums[-1]) if len(nums)>=2 else None)
    if spec is None and coll is None:
        in_loans=False
        for line in lines:
            ll=line.lower()
            if re.search(r"impairment allowances for loans",ll): in_loans=True; continue
            if re.search(r"impairment allowances for other",ll): in_loans=False; continue
            if in_loans:
                nums=trailing_nums(line)
                if len(nums)>=2:
                    if re.search(r"collective",ll) and coll is None: coll=(abs(nums[-2]),abs(nums[-1]))
                    elif re.search(r"specific",ll) and spec is None: spec=(abs(nums[-2]),abs(nums[-1]))
    return {"spec":spec,"coll":coll}

def get_lmr_cfr(lines, pdf_bytes):
    lmr = find_two(lines, r"average\s+(liquidity\s+maintenance|lmr)")
    cfr = find_two(lines, r"average\s+(core\s+funding|cfr)")
    if not(lmr and cfr):
        ol = ocr_all(pdf_bytes)
        if not lmr: lmr = find_two(ol, r"average.*lmr|lmr.*%")
        if not cfr: cfr = find_two(ol, r"average.*cfr|cfr.*%")
    return lmr, cfr

def get_description(lines):
    """Extract entity name and a 1-2 sentence description from early pages."""
    entity, desc_parts = None, []
    in_desc = False
    for line in lines:
        ll = line.lower()
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean = re.sub(r"[^a-zA-Z0-9\s,&\.\-/()\!:@']+"," ",clean).strip()
        clean = re.sub(r"\s+"," ",clean).strip()
        if not clean or len(clean)<8: continue
        # Entity name: look for "X Hong Kong Branch" style
        if not entity and re.search(r"hong kong branch", ll) and len(clean)>15:
            candidate = re.sub(r"\s+"," ",clean).strip()
            if len(candidate.split())>=3:
                entity = candidate[:120]
        # Description: full English sentences about the institution
        if re.search(r"organized under|incorporated in|share capital|liability company|registered office", ll):
            if len(clean.split())>=8:
                desc_parts.append(clean)
        if len(desc_parts)>=2: break
    desc = " ".join(desc_parts[:2])
    if desc and len(desc)>200: desc = desc[:200].rsplit(" ",1)[0]+"…"
    return entity, desc

def get_period(lines):
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        if re.search(r"(year|period|half.year)\s+ended|for the year|as at", clean, re.IGNORECASE):
            if re.search(r"\d{4}", clean):
                return re.sub(r"\s+"," ",clean).strip()[:80]
    return ""

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────
def run(pdf_bytes):
    pages = extract_pages(pdf_bytes)
    all_lines=[]
    for _,lines,_ in pages: all_lines+=lines
    full_text = "\n".join(all_lines)
    unit_label, multiplier = detect_unit(full_text)
    ta     = find_two(all_lines, r"total\s+assets|總資產")
    tl     = find_two(all_lines, r"total\s+liabilities|總負債")
    profit = find_two(all_lines, r"profit\s+after\s+tax|餘稅後盈利")
    prov   = get_provisions(all_lines)
    lmr, cfr = get_lmr_cfr(all_lines, pdf_bytes)
    ai     = parse_bs(all_lines, "assets")
    li     = parse_bs(all_lines, "liabilities")
    entity, desc = get_description(all_lines)
    period = get_period(all_lines)
    return {"unit_label":unit_label, "multiplier":multiplier,
            "ta":ta, "tl":tl, "profit":profit,
            "spec":prov["spec"], "coll":prov["coll"],
            "lmr":lmr, "cfr":cfr,
            "asset_items":ai, "liab_items":li,
            "entity":entity, "desc":desc, "period":period,
            "raw_lines":all_lines}

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<h1>HKMA Financial Disclosure Reader</h1>", unsafe_allow_html=True)
uploaded = st.file_uploader("Upload HKMA Key Financial Information Disclosure PDF", type="pdf")

if not uploaded:
    st.markdown("""
    <div style="margin-top:40px;padding:40px;border:1px dashed #ddd;text-align:center;background:#fafafa">
      <div style="font-size:0.68rem;letter-spacing:0.1em;text-transform:uppercase;color:#ccc;margin-bottom:6px;">
        Drop a disclosure PDF to begin
      </div>
      <div style="font-size:0.7rem;color:#ddd;">
        Supports any HKMA-format bank disclosure — JPMorgan, CA-CIB, BNP Paribas, etc.
      </div>
    </div>
    """, unsafe_allow_html=True)

if uploaded:
    pdf_bytes = uploaded.read()
    with st.spinner("Extracting…"):
        d = run(pdf_bytes)

    ul      = d["unit_label"]
    mult    = d["multiplier"]
    ta, tl  = d["ta"], d["tl"]
    spec    = d["spec"]
    coll    = d["coll"]
    lmr     = d["lmr"]
    cfr     = d["cfr"]
    prof    = d["profit"]
    ai      = d["asset_items"]
    li      = d["liab_items"]
    entity  = d["entity"] or uploaded.name.replace(".pdf","").replace("_"," ").upper()
    desc    = d["desc"] or ""
    period  = d["period"] or ""

    tot_prov = None
    if spec and coll:
        c2 = (spec[1]+coll[1]) if spec[1] and coll[1] else None
        tot_prov = (spec[0]+coll[0], c2)
    elif coll: tot_prov = coll
    elif spec: tot_prov = spec

    # ── Page header ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="pg-header">
      <div class="pg-bank">{entity}</div>
      <div class="pg-meta">HKMA Key Financial Disclosure<br><span>{period}</span></div>
    </div>
    <div class="unit-tag">Figures reported in {ul}</div>
    """, unsafe_allow_html=True)

    # ── Description ────────────────────────────────────────────────────────
    if desc:
        st.markdown(f"""
        <div class="desc-block">
          <div class="desc-text">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Snapshot KPIs ──────────────────────────────────────────────────────
    def kpi_block(label, raw_val, raw_prior, is_ratio=False):
        if raw_val is None: return ""
        display = f"{raw_val:.2f}%" if is_ratio else f"HKD {fmt_snapshot(raw_val, mult)}"
        if raw_prior is not None:
            if is_ratio:
                chg = round(raw_val - raw_prior, 2)
            else:
                chg = pct_chg(raw_val, raw_prior)
            if chg is not None:
                sign = "+" if chg>0 else ""
                sfx  = "pp" if is_ratio else "%"
                css  = "kpi-chg-pos" if chg>0 else "kpi-chg-neg"
                chg_html = f'<div class="{css}">{sign}{chg:.2f}{sfx} vs prior</div>'
            else:
                chg_html = ""
        else:
            chg_html = ""
        return f"""<div class="kpi">
          <div class="kpi-label">{label}</div>
          <div class="kpi-val">{display}</div>
          {chg_html}
        </div>"""

    kpis = ""
    if ta:        kpis += kpi_block("Total Assets",      ta[0],        ta[1])
    if prof:      kpis += kpi_block("Profit after Tax",  prof[0],      prof[1])
    if lmr:       kpis += kpi_block("Avg LMR",           lmr[0],       lmr[1],  is_ratio=True)
    if cfr:       kpis += kpi_block("Avg CFR",           cfr[0],       cfr[1],  is_ratio=True)
    if tot_prov:  kpis += kpi_block("Total Provisions",  tot_prov[0],  tot_prov[1])

    if kpis:
        st.markdown(f'<div class="snapshot">{kpis}</div>', unsafe_allow_html=True)

    # ── Liquidity ──────────────────────────────────────────────────────────
    st.markdown("<h2>Liquidity</h2>", unsafe_allow_html=True)
    lpp = round(lmr[0]-lmr[1],2) if lmr else None
    cpp = round(cfr[0]-cfr[1],2) if cfr else None
    st.markdown(f"""
    <div class="ratio-grid">
      <div class="ratio-card">
        <div class="ratio-label">3-Month Average LMR</div>
        <div>
          <span class="ratio-main">{f"{lmr[0]:.2f}%" if lmr else "—"}</span>
          <span class="ratio-prior">{f"prev {lmr[1]:.2f}%" if lmr else ""}</span>
        </div>
        <div style="margin-top:6px">{pp_html(lpp)}</div>
      </div>
      <div class="ratio-card">
        <div class="ratio-label">3-Month Average CFR</div>
        <div>
          <span class="ratio-main">{f"{cfr[0]:.2f}%" if cfr else "—"}</span>
          <span class="ratio-prior">{f"prev {cfr[1]:.2f}%" if cfr else ""}</span>
        </div>
        <div style="margin-top:6px">{pp_html(cpp)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key financials ─────────────────────────────────────────────────────
    st.markdown("<h2>Key Financials</h2>", unsafe_allow_html=True)
    kf_rows = [
        ("Profit after taxation", prof),
        ("Total assets",          ta),
        ("Total liabilities",     tl),
        ("Specific provisions",   spec),
        ("Collective provisions", coll),
        ("Total provisions",      tot_prov),
    ]
    rows_html = ""
    for label, pair in kf_rows:
        if pair:
            c, p = pair[0], pair[1]
            rows_html += f"<tr><td>{label}</td><td>{fmt_n(c)}</td><td>{fmt_n(p)}</td><td>{fmt_chg(pct_chg(c,p))}</td></tr>"
        else:
            rows_html += f'<tr><td class="muted">{label}</td><td class="muted">—</td><td class="muted">—</td><td class="muted">—</td></tr>'
    st.markdown(f"""
    <table>
      <thead><tr><th>Metric</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # ── Concentration top 3 ────────────────────────────────────────────────
    def render_top3(items, total_pair, title):
        if not items or not total_pair: return
        tc, tp = total_pair[0], total_pair[1] if total_pair[1] else None
        valid  = sorted([x for x in items if x["curr"] and x["curr"]>0],
                        key=lambda x: x["curr"], reverse=True)[:3]
        st.markdown(f"<h2>{title} — Top 3</h2>", unsafe_allow_html=True)
        rows_h = ""
        for i, x in enumerate(valid, 1):
            pc = round(x["curr"]/tc*100, 2) if tc else 0
            pp = round(x["prior"]/tp*100, 2) if tp and x.get("prior") else None
            rows_h += f"""<tr>
              <td><span class="rank">{i}</span>{x['label']}</td>
              <td><b>{pc:.2f}%</b></td>
              <td class="muted">{fmt_n(x['curr'])}</td>
              <td>{"<span class='muted'>—</span>" if pp is None else f"{pp:.2f}%"}</td>
              <td class="muted">{fmt_n(x.get('prior'))}</td>
            </tr>"""
        st.markdown(f"""
        <table>
          <thead><tr>
            <th style="text-align:left">Item</th>
            <th>Curr %</th><th>Current ({ul})</th>
            <th>Prior %</th><th>Prior ({ul})</th>
          </tr></thead>
          <tbody>{rows_h}</tbody>
        </table>
        """, unsafe_allow_html=True)

    render_top3(ai, ta, "Asset Concentration")
    render_top3(li, tl, "Liability Concentration")

    # ── Full breakdown ─────────────────────────────────────────────────────
    st.markdown('<hr class="rule">', unsafe_allow_html=True)
    st.markdown("<h2>Full Balance Sheet Breakdown</h2>", unsafe_allow_html=True)

    def render_full(items, total_pair, title):
        if not items or not total_pair: return
        tc, tp = total_pair[0], total_pair[1] if total_pair[1] else None
        valid  = sorted([x for x in items if x["curr"] is not None],
                        key=lambda x: x["curr"], reverse=True)
        st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
        rows_h = ""
        for x in valid:
            pc = round(x["curr"]/tc*100, 2) if tc and x["curr"] else None
            pp = round(x["prior"]/tp*100, 2) if tp and x.get("prior") else None
            rows_h += f"""<tr>
              <td>{x['label']}</td>
              <td>{fmt_n(x['curr'])}</td>
              <td>{"<span class='muted'>—</span>" if pc is None else f"<b>{pc:.2f}%</b>"}</td>
              <td class="muted">{fmt_n(x.get('prior'))}</td>
              <td>{"<span class='muted'>—</span>" if pp is None else f"{pp:.2f}%"}</td>
            </tr>"""
        st.markdown(f"""
        <table>
          <thead><tr>
            <th style="text-align:left">Item</th>
            <th>Current ({ul})</th><th>% of Total</th>
            <th>Prior ({ul})</th><th>% of Total (Prior)</th>
          </tr></thead>
          <tbody>{rows_h}</tbody>
        </table>
        """, unsafe_allow_html=True)

    render_full(ai, ta, "Assets")
    render_full(li, tl, "Liabilities")

    # ── Export ─────────────────────────────────────────────────────────────
    st.markdown('<hr class="rule">', unsafe_allow_html=True)
    export=[]
    for label,pair in kf_rows:
        if pair:
            export.append({"Section":"Key Financials","Item":label,
                           "Current":pair[0],"Prior":pair[1],"Change%":pct_chg(pair[0],pair[1])})
    if lmr: export.append({"Section":"Liquidity","Item":"Avg LMR (%)","Current":lmr[0],"Prior":lmr[1],"Change pp":lpp})
    if cfr: export.append({"Section":"Liquidity","Item":"Avg CFR (%)","Current":cfr[0],"Prior":cfr[1],"Change pp":cpp})
    for x in sorted(ai, key=lambda x:x["curr"] or 0, reverse=True):
        pct = round(x["curr"]/ta[0]*100,2) if ta and x["curr"] else None
        export.append({"Section":"Assets","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
    for x in sorted(li, key=lambda x:x["curr"] or 0, reverse=True):
        pct = round(x["curr"]/tl[0]*100,2) if tl and x["curr"] else None
        export.append({"Section":"Liabilities","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
    csv = pd.DataFrame(export).to_csv(index=False).encode("utf-8")
    st.download_button("↓  Export CSV", data=csv,
                       file_name=f"{uploaded.name.replace('.pdf','')}_metrics.csv",
                       mime="text/csv")

    with st.expander("Debug — raw extracted lines"):
        st.text("\n".join(d["raw_lines"][:300]))
