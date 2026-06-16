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

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Force light mode everywhere ── */
html, body, [class*="css"],
[data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], .main, .block-container,
[data-testid="stVerticalBlock"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #f7f7f7 !important;
    color: #1a1a1a !important;
}
.stApp, [data-testid="stAppViewContainer"] { background: #f7f7f7 !important; }
p, span, div, td, th, label, li { color: #1a1a1a !important; }

/* ── Main content area ── */
.block-container {
    max-width: 900px !important;
    padding: 2rem 2rem 4rem !important;
    background: #f7f7f7 !important;
}

/* ── Typography ── */
h1 { color: #E60028 !important; font-weight: 700 !important;
     font-size: 1.15rem !important; letter-spacing: .12em !important;
     text-transform: uppercase !important;
     border-bottom: 2px solid #E60028 !important;
     padding-bottom: 10px; margin-bottom: 2px !important; }
h2 { color: #1a1a1a !important; font-weight: 700 !important;
     font-size: .72rem !important; letter-spacing: .14em !important;
     text-transform: uppercase !important;
     margin-top: 32px !important; margin-bottom: 8px !important;
     padding-bottom: 5px !important; border-bottom: 1px solid #ddd !important; }
h3 { color: #1a1a1a !important; font-weight: 600 !important;
     font-size: .7rem !important; letter-spacing: .12em !important;
     text-transform: uppercase !important;
     margin-top: 28px !important; margin-bottom: 6px !important; }

/* ── Top header strip ── */
.page-header {
    display: flex; justify-content: space-between; align-items: flex-end;
    border-bottom: 2px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 6px;
}
.page-bank { color: #E60028 !important; font-size: 1.3rem; font-weight: 700;
             letter-spacing: .04em; line-height: 1.1; }
.page-subtitle { color: #888 !important; font-size: .72rem; text-align: right;
                 line-height: 1.6; }

/* ── Company summary card ── */
.summary-card {
    background: #1a1a1a; border-left: 4px solid #E60028;
    padding: 16px 20px; margin: 14px 0 24px 0;
}
.summary-period { color: #888 !important; font-size: .66rem;
                  letter-spacing: .1em; text-transform: uppercase; margin-bottom: 10px; }
.summary-kpis { display: flex; gap: 32px; flex-wrap: wrap; }
.kpi-block { display: flex; flex-direction: column; gap: 2px; }
.kpi-label { color: #666 !important; font-size: .63rem;
             text-transform: uppercase; letter-spacing: .08em; }
.kpi-value { color: #ffffff !important; font-size: 1.05rem; font-weight: 600; }
.kpi-change-pos { color: #4caf50 !important; font-size: .72rem; }
.kpi-change-neg { color: #E60028 !important; font-size: .72rem; }
.kpi-unit { color: #555 !important; font-size: .62rem; margin-top: 2px; }

/* ── Unit badge ── */
.unit-badge {
    display: inline-block; background: #1a1a1a !important; color: #fff !important;
    font-size: .62rem; padding: 2px 9px; letter-spacing: .07em;
    text-transform: uppercase; margin-bottom: 18px;
}

/* ── Ratio cards ── */
.ratio-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 10px 0 24px; }
.ratio-card {
    background: #ffffff !important; border: 1px solid #e5e5e5;
    border-top: 3px solid #E60028; padding: 14px 16px;
}
.ratio-label { color: #888 !important; font-size: .63rem;
               text-transform: uppercase; letter-spacing: .09em; margin-bottom: 10px; }
.ratio-vals { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.ratio-curr { color: #1a1a1a !important; font-size: 1.35rem; font-weight: 700; }
.ratio-prior { color: #bbb !important; font-size: .8rem; }
.chg-pos { color: #1a7a3a !important; font-size: .75rem; font-weight: 600; }
.chg-neg { color: #E60028 !important; font-size: .75rem; font-weight: 600; }

/* ── Section divider ── */
.section-rule { border: none; border-top: 1px solid #e0e0e0; margin: 28px 0 0; }

/* ── Tables ── */
.tbl-wrap { margin: 8px 0 22px; }
table {
    width: 100%; border-collapse: collapse; font-size: .78rem;
    background: #ffffff !important;
}
thead tr { background: #1a1a1a !important; }
th { background: #1a1a1a !important; color: #ffffff !important;
     font-weight: 500; text-transform: uppercase;
     letter-spacing: .07em; font-size: .63rem;
     padding: 8px 12px; text-align: right; white-space: nowrap; }
th:first-child { text-align: left; }
td { padding: 7px 12px; border-bottom: 1px solid #f0f0f0;
     color: #333 !important; text-align: right;
     background: #ffffff !important; }
td:first-child { text-align: left; color: #111 !important; font-weight: 500; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fef8f8 !important; }
.pos { color: #1a7a3a !important; font-weight: 600; }
.neg { color: #E60028 !important; font-weight: 600; }
.rank-chip {
    display: inline-block; background: #E60028 !important;
    color: #fff !important; font-size: .6rem; font-weight: 700;
    padding: 1px 6px; margin-right: 6px; min-width: 18px; text-align: center;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    border: 1px dashed #ccc !important; background: #ffffff !important;
    padding: 8px !important;
}
[data-testid="stFileUploader"] label { color: #888 !important; }

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: #1a1a1a !important; border: none !important;
    color: #fff !important; font-size: .7rem; padding: 7px 18px;
    letter-spacing: .07em; text-transform: uppercase; border-radius: 0 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #E60028 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #e5e5e5 !important;
    background: #ffffff !important;
}
[data-testid="stExpander"] summary { color: #bbb !important; font-size: .7rem !important; }
[data-testid="stExpander"] p,
[data-testid="stExpander"] pre { color: #666 !important; font-size: .72rem !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #E60028 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL LABELS
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL = {
    r"cash and balances":                                       "Cash and balances with banks",
    r"balances due from exchange fund|due from exchange fund":  "Due from Exchange Fund",
    r"placements with banks":                                   "Placements with banks",
    r"amounts? due from overseas offices|due from overseas offices": "Amounts due from overseas offices",
    r"trade bills":                                             "Trade bills",
    r"certificates? of deposit held":                          "Certificates of deposit held",
    r"securities held for trading":                             "Securities held for trading",
    r"advances and other accounts":                             "Advances and other accounts",
    r"loans and receivables":                                   "Loans and receivables",
    r"investment securities":                                   "Investment securities",
    r"other investments":                                       "Other investments",
    r"property.*plant.*equipment":                              "Property, plant & equipment",
    r"deposits and balances from banks":                        "Deposits and balances from banks",
    r"balances due to exchange fund":                           "Balances due to Exchange Fund",
    r"demand deposits and current accounts|demand deposits":    "Demand deposits and current accounts",
    r"saving deposits":                                         "Saving deposits",
    r"time.*call.*notice deposits":                             "Time, call and notice deposits",
    r"amounts? due to overseas offices":                        "Amount due to overseas offices",
    r"certificates? of deposit issued":                         "Certificates of deposit issued",
    r"issued debt securities":                                  "Issued debt securities",
    r"amount payable under repo":                               "Amount payable under repo",
    r"other accounts and provisions|other liabilities":         "Other accounts / liabilities",
    r"^provisions$":                                            "Provisions",
    r"deposits from customers":                                 "Deposits from customers",
}

def canonicalize(raw):
    ll = raw.lower().strip()
    for pattern, clean in CANONICAL.items():
        if re.search(pattern, ll, re.IGNORECASE):
            return clean
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",raw)
    s = re.sub(r"\s+"," ",s).strip()
    s = re.sub(r"[,\.\-\s]+$","",s).strip()
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
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",line)
    s = re.sub(r"(\s+[\(\-]?[\d,]+[\)]?)+\s*$","",s).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]{3,}.*$","",s)
    s = re.sub(r"\(see\s+part.*$","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r",?\s*net\s+of\s+impairment\s+allowance","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

def detect_unit(text):
    if re.search(r"in millions|millions of hk|million[s]? of hong kong", text, re.IGNORECASE):
        return "HKD millions"
    if re.search(r"HK\$\s*'?\s*0{3}", text, re.IGNORECASE):
        return "HKD thousands"
    if re.search(r"'000|thousands", text, re.IGNORECASE):
        return "HKD thousands"
    return "HKD thousands (assumed)"

def is_header_noise(line):
    s = line.strip()
    if not s or len(s) < 4: return True
    if re.match(r"^[^a-zA-Z0-9\-\(]", s): return True
    if re.match(r"^[A-Z]\d+\s*$", s): return True
    return False

def extract_pages(pdf_bytes):
    pages=[]
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i,page in enumerate(pdf.pages):
            text=page.extract_text() or ""
            lines=[l.strip() for l in text.splitlines() if l.strip()]
            rows=[]
            for tbl in (page.extract_tables() or []):
                for row in tbl:
                    rows.append([c.strip() if isinstance(c,str) else (c or "") for c in row])
            pages.append((i,lines,rows))
    return pages

def ocr_all(pdf_bytes):
    if not OCR_AVAILABLE: return []
    imgs=convert_from_bytes(pdf_bytes,dpi=200)
    all_lines=[]
    for img in imgs:
        t=pytesseract.image_to_string(img)
        all_lines+=[l.strip() for l in t.splitlines() if l.strip()]
    return all_lines

# ─────────────────────────────────────────────────────────────────────────────
# BALANCE SHEET PARSER
# ─────────────────────────────────────────────────────────────────────────────
HARD_SKIP = re.compile(
    r"^total\s+(assets|liabilities)|^assets\s*$|^liabilities\s*$|"
    r"^less:\s*impairment|^impairment\s+allowances\s+for|^provision\s+for\s+impaired|"
    r"^balance\s+sheet|^section\s+[a-z]|^\d+\s*$|^page\s",
    re.IGNORECASE
)
INCOME_SKIP = re.compile(
    r"profit\s+before\s+tax|profit\s+after\s+tax|interest\s+income|interest\s+expense|"
    r"operating\s+income|operating\s+expense|taxation\s+charge|tax\s+expense|"
    r"reversal\s+of\s+impairment|net\s+write\s+(back|charge)",
    re.IGNORECASE
)
DEDUCTION_SKIP = re.compile(r"^\s*-\s+(collective|specific)\b", re.IGNORECASE)

def parse_bs(lines, section="assets"):
    items=[]
    in_section=False
    start_pat = re.compile(r"^assets\s*$|^assets\s+as\s+at",re.IGNORECASE) if section=="assets" \
                else re.compile(r"^liabilities\s*$",re.IGNORECASE)
    end_pat   = re.compile(r"total\s+assets",re.IGNORECASE) if section=="assets" \
                else re.compile(r"total\s+liabilities",re.IGNORECASE)
    for line in lines:
        s = line.strip()
        if not s: continue
        if start_pat.match(s): in_section=True; continue
        if not in_section: continue
        if end_pat.search(s): in_section=False; continue
        if HARD_SKIP.search(s) or INCOME_SKIP.search(s) or DEDUCTION_SKIP.match(s): continue
        if is_header_noise(s): continue
        nums=trailing_nums(s)
        if not nums: continue
        curr  = nums[-2] if len(nums)>=2 else nums[-1]
        prior = nums[-1] if len(nums)>=2 else None
        if curr==0 and (prior is None or prior==0): continue
        rl    = raw_label(s)
        label = canonicalize(rl)
        if not label or len(label)<2: continue
        if re.match(r"^[\d,.()\-\s]+$",label): continue
        if any(x["label"]==label for x in items): continue
        items.append({"label":label,"curr":abs(curr),"prior":abs(prior) if prior is not None else None})
    return items

# ─────────────────────────────────────────────────────────────────────────────
# TARGETED FINDERS
# ─────────────────────────────────────────────────────────────────────────────
def find_two(lines, pattern):
    for i,line in enumerate(lines):
        if re.search(pattern,line,re.IGNORECASE):
            nums=trailing_nums(line)
            if len(nums)>=2: return nums[-2],nums[-1]
            for j in range(i+1,min(i+4,len(lines))):
                nums+=trailing_nums(lines[j])
                if len(nums)>=2: return nums[-2],nums[-1]
    return None

def get_provisions(lines):
    spec,coll=None,None
    for line in lines:
        ll=line.lower()
        if re.search(r"collective\s+provision|[-–]\s*collective\b",ll):
            nums=trailing_nums(line)
            if nums and coll is None:
                coll=(abs(nums[-2] if len(nums)>=2 else nums[-1]),
                      abs(nums[-1]) if len(nums)>=2 else None)
        if re.search(r"specific\s+provision|[-–]\s*specific\b",ll):
            nums=trailing_nums(line)
            if nums and spec is None:
                spec=(abs(nums[-2] if len(nums)>=2 else nums[-1]),
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
    lmr=find_two(lines,r"average\s+(liquidity\s+maintenance|lmr)")
    cfr=find_two(lines,r"average\s+(core\s+funding|cfr)")
    if not(lmr and cfr):
        ol=ocr_all(pdf_bytes)
        if not lmr: lmr=find_two(ol,r"average.*lmr|lmr.*%")
        if not cfr: cfr=find_two(ol,r"average.*cfr|cfr.*%")
    return lmr,cfr

def get_period(lines):
    """Extract reporting period and branch description from the document."""
    period, entity = None, None
    for line in lines:
        if not period and re.search(r"(year|period|half.year)\s+ended|as at|december|june", line, re.IGNORECASE):
            if re.search(r"\d{4}", line):
                period = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
                period = re.sub(r"\s+"," ",period)[:80]
        if not entity and re.search(r"hong kong branch", line, re.IGNORECASE):
            candidate = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
            candidate = re.sub(r"[^a-zA-Z0-9\s,&\.\-/']+"," ",candidate).strip()
            if len(candidate) > 8:
                entity = candidate[:100]
    return period, entity

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def run(pdf_bytes):
    pages=extract_pages(pdf_bytes)
    all_lines=[]
    for _,lines,_ in pages: all_lines+=lines
    full_text="\n".join(all_lines)
    unit_label=detect_unit(full_text)
    ta    =find_two(all_lines,r"total\s+assets|總資產")
    tl    =find_two(all_lines,r"total\s+liabilities|總負債")
    profit=find_two(all_lines,r"profit\s+after\s+tax|餘稅後盈利")
    prov  =get_provisions(all_lines)
    lmr,cfr=get_lmr_cfr(all_lines,pdf_bytes)
    ai=parse_bs(all_lines,"assets")
    li=parse_bs(all_lines,"liabilities")
    period, entity = get_period(all_lines)
    return {"unit_label":unit_label,"ta":ta,"tl":tl,"profit":profit,
            "spec":prov["spec"],"coll":prov["coll"],"lmr":lmr,"cfr":cfr,
            "asset_items":ai,"liab_items":li,"raw_lines":all_lines,
            "period":period,"entity":entity}

# ─────────────────────────────────────────────────────────────────────────────
# FORMAT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt_n(v):
    if v is None: return "—"
    return f"{abs(v):,.0f}"

def fmt_compact(v, unit_label):
    """Show large numbers as e.g. '354.2B' or '171.6M' relative to HKD unit."""
    if v is None: return "—"
    v = abs(v)
    if "million" in unit_label.lower():
        if v >= 1_000_000: return f"{v/1_000_000:.1f}T HKD"
        if v >= 1_000:     return f"{v/1_000:.1f}B HKD"
        return f"{v:,.0f}M HKD"
    else:  # thousands
        if v >= 1_000_000_000: return f"{v/1_000_000_000:.1f}T HKD"
        if v >= 1_000_000:     return f"{v/1_000_000:.1f}B HKD"
        if v >= 1_000:         return f"{v/1_000:.1f}M HKD"
        return f"{v:,.0f}K HKD"

def pct_chg(c,p):
    if c is None or p is None or p==0: return None
    return round((c-p)/abs(p)*100,2)

def fmt_chg(v):
    if v is None: return "—"
    sign="+" if v>0 else ""
    css="pos" if v>0 else "neg"
    return f'<span class="{css}">{sign}{v:.2f}%</span>'

def pp_span(v, tag="span"):
    if v is None: return "—"
    sign="+" if v>0 else ""
    css="chg-pos" if v>0 else "chg-neg"
    return f'<{tag} class="{css}">{sign}{v:.2f}pp</{tag}>'

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<h1>HKMA DISCLOSURE READER</h1>", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Upload HKMA Key Financial Information Disclosure Statement (PDF)",
    type="pdf",
    label_visibility="visible"
)

if not uploaded:
    st.markdown("""
    <div style="margin-top:32px;padding:28px 32px;background:#fff;border:1px dashed #ddd;text-align:center;">
      <div style="color:#bbb;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">
        Drop a PDF to begin
      </div>
      <div style="color:#ddd;font-size:.7rem;">
        Supports JPMorgan, CA-CIB, BNP Paribas and other HKMA-format disclosures
      </div>
    </div>
    """, unsafe_allow_html=True)

if uploaded:
    pdf_bytes = uploaded.read()
    with st.spinner("Analysing document…"):
        d = run(pdf_bytes)

    ta, tl     = d["ta"], d["tl"]
    spec, coll = d["spec"], d["coll"]
    lmr, cfr   = d["lmr"], d["cfr"]
    prof       = d["profit"]
    ai, li     = d["asset_items"], d["liab_items"]
    ul         = d["unit_label"]
    period     = d.get("period") or ""
    entity     = d.get("entity") or uploaded.name.replace(".pdf","").replace("_"," ").upper()

    tot_prov = None
    if spec and coll:
        c2 = (spec[1]+coll[1]) if spec[1] and coll[1] else None
        tot_prov = (spec[0]+coll[0], c2)
    elif coll: tot_prov = coll
    elif spec: tot_prov = spec

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="page-header">
      <div class="page-bank">{entity}</div>
      <div class="page-subtitle">
        HKMA Key Financial Information<br>
        <span style="color:#bbb">{period}</span>
      </div>
    </div>
    <div class="unit-badge">Figures in {ul}</div>
    """, unsafe_allow_html=True)

    # ── Company summary strip ─────────────────────────────────────────────────
    def kpi(label, val, prior, unit_label, is_ratio=False):
        if val is None: return ""
        chg = pct_chg(val, prior) if not is_ratio else (round(val-prior,2) if prior else None)
        if chg is not None:
            sign = "+" if chg > 0 else ""
            css  = "kpi-change-pos" if chg > 0 else "kpi-change-neg"
            sfx  = "pp" if is_ratio else "%"
            chg_html = f'<div class="{css}">{sign}{chg:.2f}{sfx} vs prior</div>'
        else:
            chg_html = ""
        display = f"{val:.2f}%" if is_ratio else fmt_compact(val, unit_label)
        return f"""<div class="kpi-block">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{display}</div>
          {chg_html}
        </div>"""

    kpis_html = ""
    if ta:    kpis_html += kpi("Total Assets",    ta[0],   ta[1],   ul)
    if prof:  kpis_html += kpi("Profit after Tax", prof[0], prof[1], ul)
    if lmr:   kpis_html += kpi("Avg LMR",          lmr[0],  lmr[1],  ul, is_ratio=True)
    if cfr:   kpis_html += kpi("Avg CFR",          cfr[0],  cfr[1],  ul, is_ratio=True)
    if tot_prov: kpis_html += kpi("Total Provisions", tot_prov[0], tot_prov[1], ul)

    st.markdown(f"""
    <div class="summary-card">
      <div class="summary-period">Snapshot — Current period vs prior period</div>
      <div class="summary-kpis">{kpis_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Liquidity ratios ──────────────────────────────────────────────────────
    st.markdown("<h2>Liquidity</h2>", unsafe_allow_html=True)
    lmr_pp = round(lmr[0]-lmr[1],2) if lmr else None
    cfr_pp = round(cfr[0]-cfr[1],2) if cfr else None
    st.markdown(f"""
    <div class="ratio-grid">
      <div class="ratio-card">
        <div class="ratio-label">3-Month Avg Liquidity Maintenance Ratio (LMR)</div>
        <div class="ratio-vals">
          <span class="ratio-curr">{f"{lmr[0]:.2f}%" if lmr else "—"}</span>
          <span class="ratio-prior">{f"vs {lmr[1]:.2f}%" if lmr else ""}</span>
          {pp_span(lmr_pp)}
        </div>
      </div>
      <div class="ratio-card">
        <div class="ratio-label">3-Month Avg Core Funding Ratio (CFR)</div>
        <div class="ratio-vals">
          <span class="ratio-curr">{f"{cfr[0]:.2f}%" if cfr else "—"}</span>
          <span class="ratio-prior">{f"vs {cfr[1]:.2f}%" if cfr else ""}</span>
          {pp_span(cfr_pp)}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key financials ────────────────────────────────────────────────────────
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
            rows_html += f"<tr><td style='color:#bbb'>{label}</td><td style='color:#bbb'>—</td><td style='color:#bbb'>—</td><td>—</td></tr>"
    st.markdown(f"""
    <div class="tbl-wrap"><table>
      <thead><tr><th>Metric</th><th>Current</th><th>Prior</th><th>Δ</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>
    """, unsafe_allow_html=True)

    # ── Top 3 Concentration ───────────────────────────────────────────────────
    def render_top3(items, total_pair, title):
        if not items or not total_pair: return
        tc, tp = total_pair[0], total_pair[1] if total_pair[1] else None
        valid  = sorted([x for x in items if x["curr"] and x["curr"]>0],
                        key=lambda x: x["curr"], reverse=True)
        top3   = valid[:3]
        st.markdown(f"<h2>{title} — Top 3</h2>", unsafe_allow_html=True)
        rows_h = ""
        for i, x in enumerate(top3, 1):
            pc = round(x["curr"]/tc*100, 2) if tc else 0
            pp = round(x["prior"]/tp*100, 2) if tp and x.get("prior") else None
            rows_h += f"""<tr>
              <td><span class="rank-chip">{i}</span>{x['label']}</td>
              <td><b>{pc:.2f}%</b></td>
              <td style="color:#888">{fmt_n(x['curr'])}</td>
              <td>{"—" if pp is None else f"{pp:.2f}%"}</td>
              <td style="color:#888">{fmt_n(x.get('prior'))}</td>
            </tr>"""
        st.markdown(f"""
        <div class="tbl-wrap"><table>
          <thead><tr>
            <th style="text-align:left">Item</th>
            <th>Curr %</th><th>Current</th><th>Prior %</th><th>Prior</th>
          </tr></thead>
          <tbody>{rows_h}</tbody>
        </table></div>
        """, unsafe_allow_html=True)

    render_top3(ai, ta, "Asset Concentration")
    render_top3(li, tl, "Liability Concentration")

    # ── Full breakdown ────────────────────────────────────────────────────────
    st.markdown("<hr class='section-rule'>", unsafe_allow_html=True)
    st.markdown("<h2>Full Asset &amp; Liability Breakdown</h2>", unsafe_allow_html=True)

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
              <td>{"—" if pc is None else f"<b>{pc:.2f}%</b>"}</td>
              <td>{fmt_n(x.get('prior'))}</td>
              <td>{"—" if pp is None else f"{pp:.2f}%"}</td>
            </tr>"""
        st.markdown(f"""
        <div class="tbl-wrap"><table>
          <thead><tr>
            <th style="text-align:left">Item</th>
            <th>Current</th><th>% of Total</th>
            <th>Prior</th><th>% of Total (Prior)</th>
          </tr></thead>
          <tbody>{rows_h}</tbody>
        </table></div>
        """, unsafe_allow_html=True)

    render_full(ai, ta, "Assets")
    render_full(li, tl, "Liabilities")

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown("<hr class='section-rule'>", unsafe_allow_html=True)
    export = []
    for label, pair in kf_rows:
        if pair:
            export.append({"Section":"Key Financials","Item":label,
                           "Current":pair[0],"Prior":pair[1],"Change%":pct_chg(pair[0],pair[1])})
    if lmr: export.append({"Section":"Liquidity","Item":"Avg LMR","Current":f"{lmr[0]}%","Prior":f"{lmr[1]}%","Change pp":lmr_pp})
    if cfr: export.append({"Section":"Liquidity","Item":"Avg CFR","Current":f"{cfr[0]}%","Prior":f"{cfr[1]}%","Change pp":cfr_pp})
    for x in sorted(ai, key=lambda x: x["curr"] or 0, reverse=True):
        pct = round(x["curr"]/ta[0]*100,2) if ta and x["curr"] else None
        export.append({"Section":"Assets","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
    for x in sorted(li, key=lambda x: x["curr"] or 0, reverse=True):
        pct = round(x["curr"]/tl[0]*100,2) if tl and x["curr"] else None
        export.append({"Section":"Liabilities","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
    csv = pd.DataFrame(export).to_csv(index=False).encode("utf-8")
    st.download_button("↓  Export CSV", data=csv,
                       file_name=f"{uploaded.name.replace('.pdf','')}_metrics.csv",
                       mime="text/csv")

    with st.expander("Debug — raw extracted lines"):
        st.text("\n".join(d["raw_lines"][:300]))

