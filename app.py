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

# ── CSS: SocGen black/white/red, no emojis ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0a;
    color: #f0f0f0;
}
.stApp { background-color: #0a0a0a; }

h1 { color: #E60028; font-weight: 600; font-size: 1.4rem; letter-spacing: 0.04em; border-bottom: 2px solid #E60028; padding-bottom: 8px; margin-bottom: 4px; }
h2, h3 { color: #f0f0f0; font-weight: 500; font-size: 0.9rem; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 28px; margin-bottom: 6px; }

/* Header bar */
.header-bar { display: flex; justify-content: space-between; align-items: baseline;
    border-bottom: 1px solid #333; padding-bottom: 6px; margin-bottom: 20px; }
.bank-name { color: #E60028; font-size: 1.1rem; font-weight: 600; letter-spacing: 0.05em; }
.header-meta { color: #888; font-size: 0.78rem; }

/* Ratio cards */
.ratio-row { display: flex; gap: 20px; margin: 12px 0 24px 0; }
.ratio-card { flex: 1; background: #141414; border: 1px solid #222; border-left: 3px solid #E60028;
    padding: 14px 18px; }
.ratio-label { color: #888; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
.ratio-vals { display: flex; gap: 20px; align-items: baseline; }
.ratio-curr { color: #f0f0f0; font-size: 1.3rem; font-weight: 500; }
.ratio-prior { color: #555; font-size: 0.9rem; }
.ratio-change-pos { color: #4caf50; font-size: 0.82rem; }
.ratio-change-neg { color: #E60028; font-size: 0.82rem; }

/* Main table */
table { width: 100%; border-collapse: collapse; font-size: 0.82rem; margin: 8px 0 20px 0; }
th { background: #141414; color: #888; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.07em; font-size: 0.7rem; padding: 8px 12px; border-bottom: 1px solid #2a2a2a; text-align: right; }
th:first-child { text-align: left; }
td { padding: 7px 12px; border-bottom: 1px solid #1a1a1a; color: #d0d0d0; text-align: right; }
td:first-child { text-align: left; color: #f0f0f0; }
tr:hover td { background: #111; }
.change-pos { color: #4caf50; }
.change-neg { color: #E60028; }

/* Concentration */
.conc-block { margin: 6px 0 20px 0; }
.conc-item { display: flex; align-items: baseline; gap: 10px; padding: 6px 0;
    border-bottom: 1px solid #1a1a1a; }
.conc-rank { color: #E60028; font-size: 0.72rem; font-weight: 600; min-width: 16px; }
.conc-name { color: #d0d0d0; font-size: 0.82rem; flex: 1; }
.conc-pct { color: #f0f0f0; font-size: 0.82rem; font-weight: 500; min-width: 52px; text-align: right; }
.conc-val { color: #666; font-size: 0.75rem; min-width: 120px; text-align: right; }

/* Upload area */
[data-testid="stFileUploader"] { border: 1px solid #222; background: #0e0e0e; padding: 4px; }
[data-testid="stFileUploader"] label { color: #888 !important; font-size: 0.78rem; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: transparent; border: 1px solid #E60028; color: #E60028;
    font-size: 0.75rem; padding: 6px 16px; letter-spacing: 0.05em; text-transform: uppercase; }
[data-testid="stDownloadButton"] > button:hover { background: #E60028; color: #fff; }

/* Divider */
hr { border-color: #1e1e1e; margin: 20px 0; }

/* Expander */
[data-testid="stExpander"] { border: 1px solid #222; background: #0e0e0e; }
summary { color: #555 !important; font-size: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def to_num(s):
    if not isinstance(s, str): return None
    s = s.strip().replace(",","").replace(" ","")
    s = re.sub(r"HK\$|'000|港幣千元|%","",s)
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[()$]","",s)
    try:
        v = float(s); return -v if neg else v
    except: return None

def nums_from_line(line):
    tokens = re.findall(r"\([\d,]+(?:\.\d+)?\)|[\d,]+(?:\.\d+)?",line)
    return [v for t in tokens for v in [to_num(t)] if v is not None]

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

def ocr_text(pdf_bytes):
    if not OCR_AVAILABLE: return ""
    imgs=convert_from_bytes(pdf_bytes,dpi=200)
    return "\n".join(pytesseract.image_to_string(img) for img in imgs)

def find_val(lines, rows, pattern):
    for row in rows:
        joined=" ".join(str(c) for c in row).lower()
        if re.search(pattern,joined):
            nums=[to_num(c) for c in row if to_num(c) is not None]
            if len(nums)>=2: return nums[0],nums[1]
    for i,line in enumerate(lines):
        if re.search(pattern,line,re.IGNORECASE):
            nums=nums_from_line(line)
            if len(nums)>=2: return nums[0],nums[1]
            for j in range(i+1,min(i+4,len(lines))):
                nums+=nums_from_line(lines[j])
                if len(nums)>=2: return nums[0],nums[1]
    return None

def get_provisions(lines):
    res={"spec_loans":None,"coll_loans":None}
    in_loans=False
    for line in lines:
        ll=line.lower()
        if re.search(r"impairment allowances for loans and advances",ll):
            in_loans=True; continue
        if re.search(r"impairment allowances for other claims",ll):
            in_loans=False; continue
        if in_loans and len(nums_from_line(line))>=2:
            nums=nums_from_line(line)
            if re.search(r"collective|組合",ll) and res["coll_loans"] is None:
                res["coll_loans"]=(abs(nums[0]),abs(nums[1]))
            elif re.search(r"specific|特定",ll) and res["spec_loans"] is None:
                res["spec_loans"]=(abs(nums[0]),abs(nums[1]))
    return res

def get_lmr_cfr(lines,pdf_bytes):
    lmr=find_val(lines,[],r"average\s+lmr|liquidity maintenance ratio")
    cfr=find_val(lines,[],r"average\s+cfr|core funding ratio")
    if not (lmr and cfr):
        raw=ocr_text(pdf_bytes)
        ol=[l.strip() for l in raw.splitlines() if l.strip()]
        if not lmr: lmr=find_val(ol,[],r"average\s+lmr|lmr")
        if not cfr: cfr=find_val(ol,[],r"average\s+cfr|cfr")
    return lmr,cfr

def get_profit(lines,rows):
    return find_val(lines,rows,r"profit after tax|餘稅後盈利")

ASSET_ITEMS=[
    ("Amounts due from overseas offices",    r"amounts due from overseas offices"),
    ("Advances and other accounts",          r"advances and other accounts"),
    ("Securities held for trading",          r"securities held for trading"),
    ("Investment securities",                r"investment securities"),
    ("Placements with banks (1-12m)",        r"placements with banks maturing"),
    ("Cash and balances with banks",         r"cash and balances with banks"),
    ("Certificates of deposit held",         r"certificates of deposit held"),
    ("Trade bills",                          r"trade bills"),
    ("Other investments",                    r"other investments"),
    ("Balances due from Exchange Fund",      r"balances due from exchange fund"),
    ("Property, plant and equipment",        r"property.*plant.*equipment"),
]
LIABILITY_ITEMS=[
    ("Time, call and notice deposits",       r"time.*call.*notice deposits"),
    ("Saving deposits",                      r"saving deposits"),
    ("Other accounts and provisions",        r"other accounts and provisions"),
    ("Deposits and balances from banks",     r"deposits and balances from banks"),
    ("Demand deposits / current accounts",   r"demand deposits and current accounts"),
    ("Amount due to overseas offices",       r"amount due to overseas offices"),
    ("Balances due to Exchange Fund",        r"balances due to exchange fund"),
    ("Amount payable under repo",            r"amount payable under repo"),
]

def get_concentration(lines,rows,items,total):
    found=[]
    for label,pat in items:
        hit=find_val(lines,rows,pat)
        if hit and total:
            found.append({"item":label,"curr":hit[0],"prior":hit[1],
                          "pct_curr":round(abs(hit[0])/total[0]*100,2),
                          "pct_prior":round(abs(hit[1])/total[1]*100,2)})
    found.sort(key=lambda x:abs(x["curr"]),reverse=True)
    return found[:3]

# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────
def run(pdf_bytes):
    pages=extract_pages(pdf_bytes)
    all_lines,all_rows=[],[]
    for _,lines,rows in pages:
        all_lines+=lines; all_rows+=rows

    data={}
    data["profit"]    = get_profit(all_lines,all_rows)
    data["ta"]        = find_val(all_lines,all_rows,r"total\s+assets|總資產")
    data["tl"]        = find_val(all_lines,all_rows,r"total\s+liabilities|總負債")
    prov              = get_provisions(all_lines)
    data["spec"]      = prov["spec_loans"]
    data["coll"]      = prov["coll_loans"]
    data["lmr"],data["cfr"] = get_lmr_cfr(all_lines,pdf_bytes)
    data["asset_conc"]= get_concentration(all_lines,all_rows,ASSET_ITEMS,data["ta"]) if data["ta"] else []
    data["liab_conc"] = get_concentration(all_lines,all_rows,LIABILITY_ITEMS,data["tl"]) if data["tl"] else []
    return data

# ─────────────────────────────────────────────────────────────────────────────
# FORMATTING
# ─────────────────────────────────────────────────────────────────────────────
def fmt_num(v):
    if v is None: return "—"
    return f"{abs(v):,.0f}"

def fmt_pct(v):
    if v is None: return "—"
    sign="+" if v>0 else ""
    css="change-pos" if v>0 else "change-neg"
    return f'<span class="{css}">{sign}{v:.2f}%</span>'

def fmt_pp(v):
    if v is None: return "—"
    sign="+" if v>0 else ""
    css="change-pos" if v>0 else "change-neg"
    return f'<span class="{css}">{sign}{v:.2f}pp</span>'

def pct_chg(curr,prior):
    if curr is None or prior is None or prior==0: return None
    return round((curr-prior)/abs(prior)*100,2)

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<h1>HKMA DISCLOSURE READER</h1>", unsafe_allow_html=True)

uploaded=st.file_uploader("Upload HKMA Key Financial Information Disclosure Statement (PDF)",type="pdf")

if uploaded:
    pdf_bytes=uploaded.read()
    with st.spinner(""):
        d=run(pdf_bytes)

    bank=uploaded.name.replace(".pdf","").replace("_"," ").upper()
    ta,tl=d["ta"],d["tl"]
    spec,coll=d["spec"],d["coll"]
    lmr,cfr=d["lmr"],d["cfr"]
    profit=d["profit"]

    tot_prov=None
    if spec and coll:
        tot_prov=((spec[0]+coll[0]),(spec[1]+coll[1]))

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="header-bar">
      <span class="bank-name">{bank}</span>
      <span class="header-meta">Source: HKMA &nbsp;|&nbsp; HKD $'000</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Liquidity ratios ──────────────────────────────────────────────────────
    st.markdown("<h3>Liquidity Ratios — Q4 YoY</h3>", unsafe_allow_html=True)
    lmr_curr = f"{lmr[0]:.2f}%" if lmr else "—"
    lmr_prior= f"{lmr[1]:.2f}%" if lmr else "—"
    lmr_pp   = round(lmr[0]-lmr[1],2) if lmr else None
    cfr_curr = f"{cfr[0]:.2f}%" if cfr else "—"
    cfr_prior= f"{cfr[1]:.2f}%" if cfr else "—"
    cfr_pp   = round(cfr[0]-cfr[1],2) if cfr else None

    def pp_span(v):
        if v is None: return "—"
        sign="+" if v>0 else ""
        css="ratio-change-pos" if v>0 else "ratio-change-neg"
        return f'<span class="{css}">{sign}{v:.2f}pp</span>'

    st.markdown(f"""
    <div class="ratio-row">
      <div class="ratio-card">
        <div class="ratio-label">3m Liquidity Maintenance Ratio (LMR)</div>
        <div class="ratio-vals">
          <span class="ratio-curr">{lmr_curr}</span>
          <span class="ratio-prior">{lmr_prior} prior</span>
          {pp_span(lmr_pp)}
        </div>
      </div>
      <div class="ratio-card">
        <div class="ratio-label">3m Core Funding Ratio (CFR)</div>
        <div class="ratio-vals">
          <span class="ratio-curr">{cfr_curr}</span>
          <span class="ratio-prior">{cfr_prior} prior</span>
          {pp_span(cfr_pp)}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main table ────────────────────────────────────────────────────────────
    st.markdown("<h3>Key Financials — Half-Year</h3>", unsafe_allow_html=True)

    rows_data=[
        ("Profit after taxation",  profit),
        ("Total assets",           ta),
        ("Total liabilities",      tl),
        ("Specific provisions",    spec),
        ("Collective provisions",  coll),
        ("Total provisions",       tot_prov),
    ]

    rows_html=""
    for label,(pair) in rows_data:
        if pair:
            c,p=pair[0],pair[1]
            rows_html+=f"""<tr>
              <td>{label}</td>
              <td>{fmt_num(c)}</td>
              <td>{fmt_num(p)}</td>
              <td>{fmt_pct(pct_chg(c,p))}</td>
            </tr>"""
        else:
            rows_html+=f"<tr><td>{label}</td><td>—</td><td>—</td><td>—</td></tr>"

    st.markdown(f"""
    <table>
      <thead><tr>
        <th>Item</th><th>Current</th><th>Prior</th><th>Change</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # ── Concentration ─────────────────────────────────────────────────────────
    def conc_block(items,period_label):
        html=f'<div style="color:#888;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px;">{period_label}</div>'
        html+='<div class="conc-block">'
        for i,a in enumerate(items,1):
            html+=f"""<div class="conc-item">
              <span class="conc-rank">#{i}</span>
              <span class="conc-name">{a['item']}</span>
              <span class="conc-pct">{a['pct_curr']:.2f}%</span>
              <span class="conc-val">HKD {fmt_num(a['curr'])}</span>
            </div>"""
        html+="</div>"
        return html

    if d["asset_conc"]:
        st.markdown("<h3>Asset Concentration — Top 3</h3>", unsafe_allow_html=True)
        st.markdown(conc_block(d["asset_conc"],"Current period"),unsafe_allow_html=True)

    if d["liab_conc"]:
        st.markdown("<h3>Liability Concentration — Top 3</h3>", unsafe_allow_html=True)
        st.markdown(conc_block(d["liab_conc"],"Current period"),unsafe_allow_html=True)

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown("<hr>",unsafe_allow_html=True)
    export_rows=[]
    for label,pair in rows_data:
        if pair:
            export_rows.append({"Metric":label,"Current":pair[0],"Prior":pair[1],
                                 "Change %":pct_chg(pair[0],pair[1])})
    if lmr:
        export_rows.append({"Metric":"Average LMR","Current":f"{lmr[0]}%","Prior":f"{lmr[1]}%","Change %":None,"Change pp":lmr_pp})
    if cfr:
        export_rows.append({"Metric":"Average CFR","Current":f"{cfr[0]}%","Prior":f"{cfr[1]}%","Change %":None,"Change pp":cfr_pp})
    for a in d["asset_conc"]:
        export_rows.append({"Metric":f"Top asset: {a['item']}","Current":a["curr"],"Prior":a["prior"],"Concentration %":a["pct_curr"]})
    for l in d["liab_conc"]:
        export_rows.append({"Metric":f"Top liability: {l['item']}","Current":l["curr"],"Prior":l["prior"],"Concentration %":l["pct_curr"]})

    csv=pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8")
    st.download_button("DOWNLOAD CSV",data=csv,
                       file_name=f"{uploaded.name.replace('.pdf','')}_metrics.csv",mime="text/csv")

    with st.expander("raw extracted lines"):
        all_lines_flat=[]
        for _,lines,_ in extract_pages(pdf_bytes):
            all_lines_flat+=lines
        st.text("\n".join(all_lines_flat[:300]))
