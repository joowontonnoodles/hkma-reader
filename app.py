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

# ── SocGen white/black/red CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; background:#ffffff; color:#1a1a1a; }
.stApp { background:#ffffff; }
h1 { color:#E60028; font-weight:700; font-size:1.3rem; letter-spacing:.04em;
     border-bottom:2px solid #E60028; padding-bottom:8px; margin-bottom:4px; }
h2,h3 { color:#1a1a1a; font-weight:600; font-size:.76rem; letter-spacing:.1em;
         text-transform:uppercase; margin-top:28px; margin-bottom:6px;
         border-bottom:1px solid #e8e8e8; padding-bottom:4px; }
.header-bar { display:flex; justify-content:space-between; align-items:baseline;
    border-bottom:2px solid #1a1a1a; padding-bottom:8px; margin-bottom:20px; }
.bank-name { color:#E60028; font-size:1.05rem; font-weight:700; letter-spacing:.05em; }
.header-meta { color:#999; font-size:.74rem; }
.ratio-row { display:flex; gap:16px; margin:12px 0 24px 0; }
.ratio-card { flex:1; background:#fafafa; border:1px solid #e8e8e8;
              border-left:4px solid #E60028; padding:14px 18px; }
.ratio-label { color:#888; font-size:.66rem; text-transform:uppercase; letter-spacing:.09em; margin-bottom:8px; }
.ratio-vals { display:flex; gap:18px; align-items:baseline; flex-wrap:wrap; }
.ratio-curr { color:#1a1a1a; font-size:1.2rem; font-weight:600; }
.ratio-prior { color:#bbb; font-size:.82rem; }
.chg-pos { color:#1a7a3a; font-size:.78rem; font-weight:500; }
.chg-neg { color:#E60028; font-size:.78rem; font-weight:500; }
table { width:100%; border-collapse:collapse; font-size:.79rem; margin:8px 0 18px 0; }
th { background:#1a1a1a; color:#ffffff; font-weight:500; text-transform:uppercase;
     letter-spacing:.07em; font-size:.65rem; padding:8px 10px; text-align:right; }
th:first-child { text-align:left; }
td { padding:6px 10px; border-bottom:1px solid #f0f0f0; color:#444; text-align:right; }
td:first-child { text-align:left; color:#1a1a1a; }
tr:hover td { background:#fff5f5; }
.pos { color:#1a7a3a; font-weight:500; } .neg { color:#E60028; font-weight:500; }
.conc-item { display:flex; align-items:baseline; gap:10px; padding:6px 0; border-bottom:1px solid #f0f0f0; }
.conc-rank { color:#E60028; font-size:.7rem; font-weight:700; min-width:20px; }
.conc-name { color:#333; font-size:.8rem; flex:1; }
.conc-pct  { color:#1a1a1a; font-size:.82rem; font-weight:700; min-width:58px; text-align:right; }
.conc-val  { color:#aaa; font-size:.74rem; min-width:130px; text-align:right; }
.unit-badge { background:#1a1a1a; color:#fff; font-size:.66rem; padding:2px 10px;
              border-radius:2px; display:inline-block; margin-bottom:16px; letter-spacing:.06em; text-transform:uppercase; }
hr { border:none; border-top:1px solid #e8e8e8; margin:24px 0; }
[data-testid="stFileUploader"] { border:1px solid #e0e0e0; background:#fafafa; padding:4px; }
[data-testid="stDownloadButton"] > button { background:#1a1a1a; border:1px solid #1a1a1a; color:#fff;
    font-size:.72rem; padding:6px 16px; letter-spacing:.06em; text-transform:uppercase; }
[data-testid="stDownloadButton"] > button:hover { background:#E60028; border-color:#E60028; }
[data-testid="stExpander"] { border:1px solid #e8e8e8 !important; background:#fafafa; }
summary { color:#bbb !important; font-size:.72rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL LABEL MAP — maps garbled/variant labels to clean display names
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL = {
    r"cash and balances":                               "Cash and balances with banks",
    r"balances due from exchange fund|due from exchange fund": "Due from Exchange Fund",
    r"placements with banks":                           "Placements with banks",
    r"amounts? due from overseas offices|due from overseas offices": "Amounts due from overseas offices",
    r"trade bills":                                     "Trade bills",
    r"certificates? of deposit held":                   "Certificates of deposit held",
    r"securities held for trading":                     "Securities held for trading",
    r"advances and other accounts":                     "Advances and other accounts",
    r"loans and receivables":                           "Loans and receivables",
    r"investment securities":                           "Investment securities",
    r"other investments":                               "Other investments",
    r"property.*plant.*equipment":                      "Property, plant and equipment",
    r"deposits and balances from banks":                "Deposits and balances from banks",
    r"balances due to exchange fund":                   "Balances due to Exchange Fund",
    r"demand deposits and current accounts|demand deposits": "Demand deposits and current accounts",
    r"saving deposits":                                 "Saving deposits",
    r"time.*call.*notice deposits":                     "Time, call and notice deposits",
    r"amounts? due to overseas offices":                "Amount due to overseas offices",
    r"certificates? of deposit issued":                 "Certificates of deposit issued",
    r"issued debt securities":                          "Issued debt securities",
    r"amount payable under repo":                       "Amount payable under repo",
    r"other accounts and provisions|other liabilities": "Other accounts / liabilities",
    r"^provisions$":                                    "Provisions",
    r"deposits from customers":                         "Deposits from customers",
}

def canonicalize(raw):
    ll = raw.lower().strip()
    for pattern, clean in CANONICAL.items():
        if re.search(pattern, ll, re.IGNORECASE):
            return clean
    # Fallback: strip non-standard chars
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
    """Remove trailing numbers, then CJK, then long noise runs."""
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",line)
    s = re.sub(r"(\s+[\(\-]?[\d,]+[\)]?)+\s*$","",s).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]{3,}.*$","",s)
    s = re.sub(r"\(see\s+part.*$","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r",?\s*net\s+of\s+impairment\s+allowance","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

def detect_unit(text):
    if re.search(r"in millions|millions of hk|million[s]? of hong kong",text,re.IGNORECASE):
        return "HKD millions"
    return "HKD thousands"

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

        nums=trailing_nums(s)
        if not nums: continue

        curr  = nums[-2] if len(nums)>=2 else nums[-1]
        prior = nums[-1] if len(nums)>=2 else None
        if curr==0 and (prior is None or prior==0): continue

        rl    = raw_label(s)
        label = canonicalize(rl)
        if not label or len(label)<2: continue
        if re.match(r"^[\d,.()\-\s]+$",label): continue

        # Deduplicate: if same canonical label already seen, skip
        if any(x["label"]==label for x in items): continue

        items.append({"label":label,"curr":abs(curr),"prior":abs(prior) if prior else None})

    return items

# ─────────────────────────────────────────────────────────────────────────────
# TARGETED FINDERS
# ─────────────────────────────────────────────────────────────────────────────
def find_two(lines, pattern):
    for i,line in enumerate(lines):
        if re.search(pattern,line,re.IGNORECASE):
            nums=trailing_nums(line)
            if len(nums)>=2: return nums[0],nums[1]
            for j in range(i+1,min(i+4,len(lines))):
                nums+=trailing_nums(lines[j])
                if len(nums)>=2: return nums[0],nums[1]
    return None

def get_provisions(lines):
    spec,coll=None,None
    for line in lines:
        ll=line.lower()
        if re.search(r"collective\s+provision|[-–]\s*collective\b",ll):
            nums=trailing_nums(line)
            if nums and coll is None:
                coll=(abs(nums[0]),abs(nums[1]) if len(nums)>=2 else None)
        if re.search(r"specific\s+provision|[-–]\s*specific\b",ll):
            nums=trailing_nums(line)
            if nums and spec is None:
                spec=(abs(nums[0]),abs(nums[1]) if len(nums)>=2 else None)
    if spec is None and coll is None:
        in_loans=False
        for line in lines:
            ll=line.lower()
            if re.search(r"impairment allowances for loans and advances",ll):
                in_loans=True; continue
            if re.search(r"impairment allowances for other claims",ll):
                in_loans=False; continue
            if in_loans:
                nums=trailing_nums(line)
                if len(nums)>=2:
                    if re.search(r"collective|組合",ll) and coll is None:
                        coll=(abs(nums[0]),abs(nums[1]))
                    elif re.search(r"specific|特定",ll) and spec is None:
                        spec=(abs(nums[0]),abs(nums[1]))
    return {"spec":spec,"coll":coll}

def get_lmr_cfr(lines, pdf_bytes):
    lmr=find_two(lines,r"average\s+(liquidity\s+maintenance|lmr)")
    cfr=find_two(lines,r"average\s+(core\s+funding|cfr)")
    if not(lmr and cfr):
        ol=ocr_all(pdf_bytes)
        if not lmr: lmr=find_two(ol,r"average.*lmr|lmr.*%")
        if not cfr: cfr=find_two(ol,r"average.*cfr|cfr.*%")
    return lmr,cfr

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXTRACTION
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
    return {"unit_label":unit_label,"ta":ta,"tl":tl,"profit":profit,
            "spec":prov["spec"],"coll":prov["coll"],"lmr":lmr,"cfr":cfr,
            "asset_items":ai,"liab_items":li,"raw_lines":all_lines}

# ─────────────────────────────────────────────────────────────────────────────
# FORMATTING
# ─────────────────────────────────────────────────────────────────────────────
def fmt_n(v):
    if v is None: return "—"
    return f"{abs(v):,.0f}"

def pct_chg(c,p):
    if c is None or p is None or p==0: return None
    return round((c-p)/abs(p)*100,2)

def fmt_chg(v):
    if v is None: return "—"
    sign="+" if v>0 else ""
    css="pos" if v>0 else "neg"
    return f'<span class="{css}">{sign}{v:.2f}%</span>'

def pp_span(v):
    if v is None: return "—"
    sign="+" if v>0 else ""
    css="chg-pos" if v>0 else "chg-neg"
    return f'<span class="{css}">{sign}{v:.2f}pp</span>'

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<h1>HKMA DISCLOSURE READER</h1>",unsafe_allow_html=True)
uploaded=st.file_uploader("Upload HKMA Key Financial Information Disclosure Statement (PDF)",type="pdf")

if uploaded:
    pdf_bytes=uploaded.read()
    with st.spinner(""):
        d=run(pdf_bytes)

    ta,tl   =d["ta"],d["tl"]
    spec,coll=d["spec"],d["coll"]
    lmr,cfr =d["lmr"],d["cfr"]
    prof    =d["profit"]
    ai,li   =d["asset_items"],d["liab_items"]
    ul      =d["unit_label"]

    tot_prov=None
    if spec and coll:
        c2=(spec[1]+coll[1]) if spec[1] and coll[1] else None
        tot_prov=(spec[0]+coll[0],c2)
    elif coll: tot_prov=coll
    elif spec: tot_prov=spec

    bank=uploaded.name.replace(".pdf","").replace("_"," ").upper()

    st.markdown(f"""
    <div class="header-bar">
      <span class="bank-name">{bank}</span>
      <span class="header-meta">Source: HKMA &nbsp;|&nbsp; {ul}</span>
    </div>
    <div class="unit-badge">{ul}</div>
    """,unsafe_allow_html=True)

    # ── Liquidity ratios ─────────────────────────────────────────────────────
    st.markdown("<h3>Liquidity Ratios — Q4 YoY</h3>",unsafe_allow_html=True)
    lmr_pp=round(lmr[0]-lmr[1],2) if lmr else None
    cfr_pp=round(cfr[0]-cfr[1],2) if cfr else None
    st.markdown(f"""
    <div class="ratio-row">
      <div class="ratio-card">
        <div class="ratio-label">3m Liquidity Maintenance Ratio (LMR)</div>
        <div class="ratio-vals">
          <span class="ratio-curr">{f"{lmr[0]:.2f}%" if lmr else "—"}</span>
          <span class="ratio-prior">{f"{lmr[1]:.2f}% prior" if lmr else ""}</span>
          {pp_span(lmr_pp)}
        </div>
      </div>
      <div class="ratio-card">
        <div class="ratio-label">3m Core Funding Ratio (CFR)</div>
        <div class="ratio-vals">
          <span class="ratio-curr">{f"{cfr[0]:.2f}%" if cfr else "—"}</span>
          <span class="ratio-prior">{f"{cfr[1]:.2f}% prior" if cfr else ""}</span>
          {pp_span(cfr_pp)}
        </div>
      </div>
    </div>
    """,unsafe_allow_html=True)

    # ── Key financials ────────────────────────────────────────────────────────
    st.markdown("<h3>Key Financials — Half-Year</h3>",unsafe_allow_html=True)
    kf_rows=[
        ("Profit after taxation",prof),
        ("Total assets",ta),("Total liabilities",tl),
        ("Specific provisions",spec),("Collective provisions",coll),
        ("Total provisions",tot_prov),
    ]
    rows_html=""
    for label,pair in kf_rows:
        if pair:
            c,p=pair[0],pair[1]
            rows_html+=f"<tr><td>{label}</td><td>{fmt_n(c)}</td><td>{fmt_n(p)}</td><td>{fmt_chg(pct_chg(c,p))}</td></tr>"
        else:
            rows_html+=f"<tr><td>{label}</td><td>—</td><td>—</td><td>—</td></tr>"
    st.markdown(f"""<table><thead><tr><th>Item</th><th>Current</th><th>Prior</th><th>Change</th></tr></thead>
    <tbody>{rows_html}</tbody></table>""",unsafe_allow_html=True)

    # ── Top 3 concentration ───────────────────────────────────────────────────
    def render_top3(items,total_pair,title):
        if not items or not total_pair: return
        total_curr=total_pair[0]
        valid=sorted([x for x in items if x["curr"] and x["curr"]>0],key=lambda x:x["curr"],reverse=True)
        top3=valid[:3]
        st.markdown(f"<h3>{title} — Top 3</h3>",unsafe_allow_html=True)
        html="<div>"
        for i,x in enumerate(top3,1):
            pct=round(x["curr"]/total_curr*100,2) if total_curr else 0
            html+=f"""<div class="conc-item">
              <span class="conc-rank">#{i}</span>
              <span class="conc-name">{x['label']}</span>
              <span class="conc-pct">{pct:.2f}%</span>
              <span class="conc-val">{fmt_n(x['curr'])}</span>
            </div>"""
        html+="</div>"
        st.markdown(html,unsafe_allow_html=True)

    render_top3(ai,ta,"Asset Concentration")
    render_top3(li,tl,"Liability Concentration")

    # ── Full breakdown ────────────────────────────────────────────────────────
    def render_full(items,total_pair,title):
        if not items or not total_pair: return
        tc,tp=total_pair[0],total_pair[1] if total_pair[1] else None
        valid=sorted([x for x in items if x["curr"] is not None],key=lambda x:x["curr"],reverse=True)
        st.markdown(f"<h3>{title}</h3>",unsafe_allow_html=True)
        rows_h=""
        for x in valid:
            pc=round(x["curr"]/tc*100,2) if tc and x["curr"] else None
            pp=round(x["prior"]/tp*100,2) if tp and x.get("prior") else None
            rows_h+=f"""<tr><td>{x['label']}</td><td>{fmt_n(x['curr'])}</td>
              <td>{"—" if pc is None else f"{pc:.2f}%"}</td>
              <td>{fmt_n(x.get('prior'))}</td>
              <td>{"—" if pp is None else f"{pp:.2f}%"}</td></tr>"""
        st.markdown(f"""<table><thead><tr>
          <th>Item</th><th>Current</th><th>% of Total</th><th>Prior</th><th>% of Total (Prior)</th>
        </tr></thead><tbody>{rows_h}</tbody></table>""",unsafe_allow_html=True)

    st.markdown("<hr>",unsafe_allow_html=True)
    render_full(ai,ta,"Full Asset Breakdown")
    render_full(li,tl,"Full Liability Breakdown")

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown("<hr>",unsafe_allow_html=True)
    export=[]
    for label,pair in kf_rows:
        if pair:
            export.append({"Section":"Key Financials","Item":label,
                           "Current":pair[0],"Prior":pair[1],"Change%":pct_chg(pair[0],pair[1])})
    if lmr: export.append({"Section":"Liquidity","Item":"Average LMR","Current":f"{lmr[0]}%","Prior":f"{lmr[1]}%","Change pp":lmr_pp})
    if cfr: export.append({"Section":"Liquidity","Item":"Average CFR","Current":f"{cfr[0]}%","Prior":f"{cfr[1]}%","Change pp":cfr_pp})
    for x in sorted(ai,key=lambda x:x["curr"] or 0,reverse=True):
        pct=round(x["curr"]/ta[0]*100,2) if ta and x["curr"] else None
        export.append({"Section":"Assets","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
    for x in sorted(li,key=lambda x:x["curr"] or 0,reverse=True):
        pct=round(x["curr"]/tl[0]*100,2) if tl and x["curr"] else None
        export.append({"Section":"Liabilities","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
    csv=pd.DataFrame(export).to_csv(index=False).encode("utf-8")
    st.download_button("DOWNLOAD CSV",data=csv,
                       file_name=f"{uploaded.name.replace('.pdf','')}_metrics.csv",mime="text/csv")

    with st.expander("raw extracted lines"):
        st.text("\n".join(d["raw_lines"][:300]))
