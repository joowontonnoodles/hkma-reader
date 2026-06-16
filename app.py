import streamlit as st
import pdfplumber
import pandas as pd
import re, io, datetime

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body,
[data-testid="stAppViewContainer"],[data-testid="stHeader"],
[data-testid="stToolbar"],[data-testid="stSidebar"],
.main,.block-container,[data-testid="stVerticalBlock"],[class*="css"] {
    font-family:'DM Sans',sans-serif !important;
    background-color:#ffffff !important; color:#111111 !important;
}
.stApp,[data-testid="stAppViewContainer"]{background:#ffffff !important;}
.block-container{max-width:860px !important;padding:2.5rem 2rem 5rem !important;}
p,span,div,li{color:#111111 !important;}
h1{font-family:'DM Sans',sans-serif !important;font-size:.72rem !important;font-weight:700 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#E60028 !important;
   border-bottom:1.5px solid #E60028 !important;padding-bottom:10px !important;margin-bottom:4px !important;}
h2{font-family:'DM Sans',sans-serif !important;font-size:.65rem !important;font-weight:600 !important;
   letter-spacing:.18em !important;text-transform:uppercase !important;color:#555555 !important;
   border-bottom:1px solid #eeeeee !important;padding-bottom:5px !important;
   margin-top:36px !important;margin-bottom:10px !important;}
h3{font-family:'DM Sans',sans-serif !important;font-size:.63rem !important;font-weight:600 !important;
   letter-spacing:.14em !important;text-transform:uppercase !important;color:#888888 !important;
   margin-top:22px !important;margin-bottom:8px !important;}
.pg-header{display:flex;justify-content:space-between;align-items:flex-end;
           border-bottom:2px solid #111111;padding-bottom:12px;margin-bottom:4px;}
.pg-bank{font-size:1.45rem;font-weight:700;color:#111111 !important;letter-spacing:-.01em;line-height:1;}
.pg-meta{font-size:.68rem;color:#999999 !important;text-align:right;line-height:1.7;}
.unit-tag{display:inline-block;font-size:.62rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
          color:#E60028 !important;border:1px solid #E60028;padding:2px 8px;margin:10px 0 20px 0;}
.desc-block{border-left:3px solid #E60028;padding:10px 14px;background:#fafafa !important;margin-bottom:28px;}
.desc-text{font-size:.78rem;color:#444444 !important;line-height:1.65;}
.snapshot{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
          gap:1px;background:#e8e8e8;border:1px solid #e8e8e8;margin-bottom:32px;}
.kpi{background:#ffffff !important;padding:14px 16px;}
.kpi-label{font-size:.6rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
           color:#999999 !important;margin-bottom:6px;}
.kpi-val{font-size:1.05rem;font-weight:700;color:#111111 !important;line-height:1;}
.kpi-chg-pos{font-size:.65rem;color:#1a7a3a !important;margin-top:4px;}
.kpi-chg-neg{font-size:.65rem;color:#E60028 !important;margin-top:4px;}
.ratio-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0 28px;}
.ratio-card{border:1px solid #e8e8e8;border-top:2.5px solid #E60028;
            padding:16px 18px;background:#ffffff !important;}
.ratio-label{font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
             color:#aaaaaa !important;margin-bottom:10px;}
.ratio-main{font-size:1.6rem;font-weight:700;color:#111111 !important;line-height:1;}
.ratio-prior{font-size:.72rem;color:#cccccc !important;margin-left:6px;}
.chg-pos{font-size:.68rem;font-weight:600;color:#1a7a3a !important;}
.chg-neg{font-size:.68rem;font-weight:600;color:#E60028 !important;}
table{width:100%;border-collapse:collapse;font-size:.77rem;margin:6px 0 20px;background:#ffffff !important;}
thead tr{border-bottom:2px solid #111111;}
th{font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999999 !important;
   background:#ffffff !important;padding:0 12px 8px;text-align:right;white-space:nowrap;}
th:first-child{text-align:left;}
td{padding:8px 12px;border-bottom:1px solid #f2f2f2;color:#222222 !important;
   text-align:right;background:#ffffff !important;}
td:first-child{text-align:left;font-weight:500;color:#111111 !important;}
tr:last-child td{border-bottom:none;}
tr:hover td{background:#fef5f5 !important;}
.pos{color:#1a7a3a !important;font-weight:600;}
.neg{color:#E60028 !important;font-weight:600;}
.muted{color:#bbbbbb !important;}
.rank{display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;
      font-size:.6rem;font-weight:700;color:#E60028 !important;border:1px solid #E60028;
      margin-right:8px;vertical-align:middle;}
.rule{border:none;border-top:1px solid #e8e8e8;margin:32px 0 0;}
[data-testid="stFileUploader"]{border:1px dashed #dddddd !important;background:#fafafa !important;padding:6px !important;}
[data-testid="stDownloadButton"]>button{background:#ffffff !important;border:1.5px solid #111111 !important;
    color:#111111 !important;font-family:'DM Sans',sans-serif !important;font-size:.68rem !important;
    font-weight:600 !important;letter-spacing:.1em !important;text-transform:uppercase !important;
    padding:8px 20px !important;border-radius:0 !important;}
[data-testid="stDownloadButton"]>button:hover{background:#E60028 !important;border-color:#E60028 !important;color:#ffffff !important;}
[data-testid="stExpander"]{border:1px solid #eeeeee !important;background:#fafafa !important;}
details summary{color:#cccccc !important;font-size:.68rem !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL LABELS
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL = {
    r"cash and balances":                                            "Cash and balances with banks",
    r"balances due from exchange fund|due from exchange fund":       "Due from Exchange Fund",
    r"placements with banks":                                        "Placements with banks",
    r"amounts? due from overseas offices|due from overseas offices": "Amounts due from overseas offices",
    r"trade bills":                                                  "Trade bills",
    r"certificates? of deposit held":                               "Certificates of deposit held",
    r"securities held for trading":                                  "Securities held for trading",
    r"advances and other accounts":                                  "Advances and other accounts",
    r"loans and receivables":                                        "Loans and receivables",
    r"investment securities":                                        "Investment securities",
    r"other investments":                                            "Other investments",
    r"property.*plant.*equipment":                                   "Property, plant & equipment",
    r"deposits and balances from banks":                             "Deposits and balances from banks",
    r"balances due to exchange fund":                                "Balances due to Exchange Fund",
    r"demand deposits and current accounts|demand deposits":         "Demand deposits and current accounts",
    r"saving deposits":                                              "Saving deposits",
    r"time.*call.*notice deposits":                                  "Time, call and notice deposits",
    r"amounts? due to overseas offices":                             "Amount due to overseas offices",
    r"certificates? of deposit issued":                              "Certificates of deposit issued",
    r"issued debt securities":                                       "Issued debt securities",
    r"amount payable under repo":                                    "Amount payable under repo",
    r"other accounts and provisions|other liabilities":              "Other accounts / liabilities",
    r"^provisions$":                                                 "Provisions",
    r"deposits from customers":                                      "Deposits from customers",
}

def canonicalize(raw):
    ll = raw.lower().strip()
    for pat, clean in CANONICAL.items():
        if re.search(pat, ll, re.IGNORECASE): return clean
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",raw)
    s = re.sub(r"\s+"," ",s).strip()
    s = re.sub(r"[,\.\-\s]+$","",s).strip()
    return s[:70].rsplit(" ",1)[0].strip() if len(s)>70 else s

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def clean_num(s):
    if not isinstance(s,str): return None
    s=s.strip().replace(",","").replace("\xa0","").replace(" ","")
    s=re.sub(r"HK\$|US\$|'000|港幣千元","",s).strip()
    if s in ("","—","-","–","Nil","nil","N/A"): return None
    neg=s.startswith("(") and s.endswith(")")
    s=re.sub(r"[()$]","",s)
    try: v=float(s); return -v if neg else v
    except: return None

def trailing_nums(line):
    tokens=re.findall(r"\([\d,]+(?:\.\d+)?\)|[\d,]+(?:\.\d+)?",line)
    return [v for t in tokens for v in [clean_num(t)] if v is not None]

def raw_label(line):
    s=re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",line)
    s=re.sub(r"(\s+[\(\-]?[\d,]+[\)]?)+\s*$","",s).strip()
    s=re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]{3,}.*$","",s)
    s=re.sub(r"\(see\s+part.*$","",s,flags=re.IGNORECASE).strip()
    s=re.sub(r",?\s*net\s+of\s+impairment\s+allowance","",s,flags=re.IGNORECASE).strip()
    s=re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

def detect_unit(lines):
    def _check(subset):
        for line in subset:
            if re.search(r"in millions|millions of hk|million[s]? of hong kong",line,re.IGNORECASE):
                return "HKD millions",1_000_000
            if re.search(r"HK\$\s*'?\s*0{3}",line,re.IGNORECASE): return "HKD thousands",1_000
            if re.search(r"'000",line,re.IGNORECASE): return "HKD thousands",1_000
        return None
    r=_check(lines[:150])
    if r: return r
    for line in lines:
        if re.search(r"HK\$\s*'?\s*0{3}|'000",line,re.IGNORECASE): return "HKD thousands",1_000
    for line in lines:
        if re.search(r"in millions|millions of hk|million[s]? of hong kong",line,re.IGNORECASE):
            return "HKD millions",1_000_000
    return "HKD thousands",1_000

def fmt_n(v): return "—" if v is None else f"{abs(v):,.0f}"
def pct_chg(c,p): return None if (c is None or p is None or p==0) else round((c-p)/abs(p)*100,2)
def fmt_chg(v):
    if v is None: return '<span class="muted">—</span>'
    return f'<span class="{"pos" if v>0 else "neg"}">{"+" if v>0 else ""}{v:.2f}%</span>'
def pp_html(v):
    if v is None: return '<span class="muted">—</span>'
    return f'<span class="{"chg-pos" if v>0 else "chg-neg"}">{"+" if v>0 else ""}{v:.2f}pp</span>'

def fmt_snapshot(v,multiplier):
    if v is None: return "—"
    hkd=abs(v)*multiplier
    if hkd>=1e12: return f"{hkd/1e12:.2f}T"
    if hkd>=1e9:  return f"{hkd/1e9:.1f}B"
    if hkd>=1e6:  return f"{hkd/1e6:.0f}M"
    return f"{hkd:,.0f}"

def is_noise(line):
    s=line.strip()
    if not s or len(s)<4: return True
    if re.match(r"^[^a-zA-Z0-9\-\(]",s): return True
    if re.match(r"^[A-Z]\d+\s*$",s): return True
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
    out=[]
    for img in imgs:
        t=pytesseract.image_to_string(img)
        out+=[l.strip() for l in t.splitlines() if l.strip()]
    return out

HARD_SKIP=re.compile(r"^total\s+(assets|liabilities)|^assets\s*$|^liabilities\s*$|^less:\s*impairment|^impairment\s+allowances\s+for|^provision\s+for\s+impaired|^balance\s+sheet|^section\s+[a-z]|^\d+\s*$|^page\s",re.IGNORECASE)
INCOME_SKIP=re.compile(r"profit\s+before\s+tax|profit\s+after\s+tax|interest\s+income|interest\s+expense|operating\s+income|operating\s+expense|taxation\s+charge|tax\s+expense|reversal\s+of\s+impairment|net\s+write\s+(back|charge)",re.IGNORECASE)
DED_SKIP=re.compile(r"^\s*-\s+(collective|specific)\b",re.IGNORECASE)

def parse_bs(lines,section="assets"):
    items=[]
    in_sec=False
    s_pat=re.compile(r"^assets\s*$|^assets\s+as\s+at",re.IGNORECASE) if section=="assets" else re.compile(r"^liabilities\s*$",re.IGNORECASE)
    e_pat=re.compile(r"total\s+assets",re.IGNORECASE) if section=="assets" else re.compile(r"total\s+liabilities",re.IGNORECASE)
    for line in lines:
        s=line.strip()
        if not s: continue
        if s_pat.match(s): in_sec=True; continue
        if not in_sec: continue
        if e_pat.search(s): in_sec=False; continue
        if HARD_SKIP.search(s) or INCOME_SKIP.search(s) or DED_SKIP.match(s): continue
        if is_noise(s): continue
        nums=trailing_nums(s)
        if not nums: continue
        curr=nums[-2] if len(nums)>=2 else nums[-1]
        prior=nums[-1] if len(nums)>=2 else None
        if curr==0 and (prior is None or prior==0): continue
        rl=raw_label(s); label=canonicalize(rl)
        if not label or len(label)<2: continue
        if re.match(r"^[\d,.()\-\s]+$",label): continue
        if any(x["label"]==label for x in items): continue
        items.append({"label":label,"curr":abs(curr),"prior":abs(prior) if prior is not None else None})
    return items

def find_two(lines,pattern):
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
                coll=(abs(nums[-2] if len(nums)>=2 else nums[-1]),abs(nums[-1]) if len(nums)>=2 else None)
        if re.search(r"specific\s+provision|[-–]\s*specific\b",ll):
            nums=trailing_nums(line)
            if nums and spec is None:
                spec=(abs(nums[-2] if len(nums)>=2 else nums[-1]),abs(nums[-1]) if len(nums)>=2 else None)
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

def get_lmr_cfr(lines,pdf_bytes):
    lmr=find_two(lines,r"average\s+(liquidity\s+maintenance|lmr)")
    cfr=find_two(lines,r"average\s+(core\s+funding|cfr)")
    if not(lmr and cfr):
        ol=ocr_all(pdf_bytes)
        if not lmr: lmr=find_two(ol,r"average.*lmr|lmr.*%")
        if not cfr: cfr=find_two(ol,r"average.*cfr|cfr.*%")
    return lmr,cfr

def get_description(lines):
    entity,desc_parts=None,[]
    for line in lines:
        ll=line.lower()
        clean=re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean=re.sub(r"[^a-zA-Z0-9\s,&\.\-/()\!:@']+"," ",clean).strip()
        clean=re.sub(r"\s+"," ",clean).strip()
        if not clean or len(clean)<8: continue
        if not entity and re.search(r"hong kong branch",ll) and len(clean)>15:
            candidate=re.sub(r"\s+"," ",clean).strip()
            if len(candidate.split())>=3: entity=candidate[:120]
        if re.search(r"organized under|incorporated in|share capital|liability company|registered office",ll):
            if len(clean.split())>=8: desc_parts.append(clean)
        if len(desc_parts)>=2: break
    desc=" ".join(desc_parts[:2])
    if desc and len(desc)>200: desc=desc[:200].rsplit(" ",1)[0]+"…"
    return entity,desc

def get_period(lines):
    for line in lines:
        clean=re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        if re.search(r"(year|period|half.year)\s+ended|for the year|as at",clean,re.IGNORECASE):
            if re.search(r"\d{4}",clean):
                return re.sub(r"\s+"," ",clean).strip()[:80]
    return ""

def run(pdf_bytes):
    pages=extract_pages(pdf_bytes)
    all_lines=[]
    for _,lines,_ in pages: all_lines+=lines
    ul,mult=detect_unit(all_lines)
    ta=find_two(all_lines,r"total\s+assets|總資產")
    tl=find_two(all_lines,r"total\s+liabilities|總負債")
    profit=find_two(all_lines,r"profit\s+after\s+tax|餘稅後盈利")
    prov=get_provisions(all_lines)
    lmr,cfr=get_lmr_cfr(all_lines,pdf_bytes)
    ai=parse_bs(all_lines,"assets")
    li=parse_bs(all_lines,"liabilities")
    entity,desc=get_description(all_lines)
    period=get_period(all_lines)
    return {"unit_label":ul,"multiplier":mult,"ta":ta,"tl":tl,"profit":profit,
            "spec":prov["spec"],"coll":prov["coll"],"lmr":lmr,"cfr":cfr,
            "asset_items":ai,"liab_items":li,"entity":entity,"desc":desc,
            "period":period,"raw_lines":all_lines}

# ─────────────────────────────────────────────────────────────────────────────
# REPORT GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def dir_word(curr, prior):
    if curr is None or prior is None: return "changed"
    return "increased" if curr > prior else "decreased" if curr < prior else "remained flat"

def conc_word(curr_pct, prior_pct):
    if curr_pct is None or prior_pct is None: return "changed"
    diff = curr_pct - prior_pct
    if abs(diff) < 0.5: return "remained broadly stable"
    return f"{'increased' if diff>0 else 'decreased'} by {abs(diff):.2f}pp"

def top3_same(curr_list, prior_list):
    if not curr_list or not prior_list: return True
    c_labels = {x["label"] for x in curr_list[:3]}
    p_labels = {x["label"] for x in prior_list[:3]}
    return c_labels == p_labels

def generate_report_html(d, filename, ul, mult):
    entity   = d["entity"] or filename
    period   = d["period"] or "Year ended 31 December 2025"
    desc     = d["desc"] or ""
    ta,tl    = d["ta"],d["tl"]
    prof     = d["profit"]
    spec,coll= d["spec"],d["coll"]
    lmr,cfr  = d["lmr"],d["cfr"]
    ai,li    = d["asset_items"],d["liab_items"]
    tc_curr  = ta[0] if ta else None
    tc_prior = ta[1] if ta else None
    tl_curr  = tl[0] if tl else None
    tl_prior = tl[1] if tl else None

    tot_prov = None
    if spec and coll:
        c2=(spec[1]+coll[1]) if spec[1] and coll[1] else None
        tot_prov=(spec[0]+coll[0],c2)
    elif coll: tot_prov=coll
    elif spec: tot_prov=spec

    ai_sorted = sorted([x for x in ai if x["curr"]], key=lambda x:x["curr"], reverse=True)
    li_sorted = sorted([x for x in li if x["curr"]], key=lambda x:x["curr"], reverse=True)
    ai_top3   = ai_sorted[:3]
    li_top3   = li_sorted[:3]

    # ── helper for concentration bullet
    def conc_bullets(items, total_curr, total_prior, period_label, is_prior=False):
        html = ""
        for x in items:
            if is_prior:
                val = x.get("prior")
                tot = total_prior
            else:
                val = x["curr"]
                tot = total_curr
            pct = round(val/tot*100,2) if val and tot else None
            pct_str = f"{pct:.2f}%" if pct is not None else "n/a"
            val_str = fmt_n(val)
            html += f"""
            <div class="bullet">
              <span class="arrow">↠</span>
              <span class="bullet-name">{x['label']}</span>
              <span class="bullet-pct">{pct_str} of total {"assets" if total_curr==tc_curr else "liabilities"}</span>
              <span class="bullet-unit">({ul}: {val_str})</span>
            </div>"""
        return html

    # ── LMR narrative
    lmr_dir = dir_word(lmr[0] if lmr else None, lmr[1] if lmr else None)
    lmr_pp  = round(lmr[0]-lmr[1],2) if lmr else None
    lmr_cov = round(lmr[0],1) if lmr else None
    cfr_dir = dir_word(cfr[0] if cfr else None, cfr[1] if cfr else None)
    cfr_pp  = round(cfr[0]-cfr[1],2) if cfr else None
    liq_min_pct = round(min(lmr[0],cfr[0]),0) if lmr and cfr else None

    lmr_text = (f"The LMR {lmr_dir} from {lmr[1]:.2f}% to {lmr[0]:.2f}%, "
                f"a change of {'+'if lmr_pp and lmr_pp>0 else ''}{lmr_pp:.2f}pp. "
                f"{entity.split()[0] if entity else 'The branch'} holds sufficient liquid assets to cover "
                f"approximately {lmr_cov:.0f}% of its liabilities maturing within one month. "
                f"The LMR remains well above the regulatory minimum of 25%.") if lmr else "LMR data not found in document."

    cfr_text = (f"The CFR {cfr_dir} from {cfr[1]:.2f}% to {cfr[0]:.2f}%, "
                f"a change of {'+'if cfr_pp and cfr_pp>0 else ''}{cfr_pp:.2f}pp. "
                f"This indicates that the branch's stable funding sources {'more than adequately cover' if cfr[0]>100 else 'cover'} "
                f"its required stable funding needs. "
                f"The CFR remains well above the regulatory minimum of 75%.") if cfr else "CFR data not found in document."

    liq_summary = (f"In terms of liquidity, {entity.split()[0] if entity else 'the branch'} is "
                   f"{'well above' if liq_min_pct and liq_min_pct>100 else 'above'} regulatory requirements for both ratios. "
                   f"The lower of the two ratios stands at {liq_min_pct:.0f}%, "
                   f"demonstrating a robust short-term liquidity buffer.") if lmr and cfr else ""

    # ── Key financials table rows
    def kf_row(label, pair):
        if not pair: return f'<tr><td>{label}</td><td class="num muted">—</td><td class="num muted">—</td><td class="num muted">—</td></tr>'
        c,p=pair[0],pair[1]
        chg=pct_chg(c,p)
        chg_str=f"{'+'if chg and chg>0 else ''}{chg:.2f}%" if chg is not None else "—"
        css="pos" if chg and chg>0 else ("neg" if chg and chg<0 else "")
        return f'<tr><td>{label}</td><td class="num">{fmt_n(c)}</td><td class="num">{fmt_n(p)}</td><td class="num {css}">{chg_str}</td></tr>'

    # ── Asset concentration commentary
    a_same = top3_same(ai_sorted, ai_sorted)  # comparing same list — always same
    a_labels_curr  = [x["label"] for x in ai_top3]
    # Check if prior ordering differs
    ai_prior = sorted([x for x in ai if x.get("prior")], key=lambda x:x["prior"], reverse=True)[:3]
    a_labels_prior = [x["label"] for x in ai_prior]
    a_same_set = set(a_labels_curr) == set(a_labels_prior)

    a_top_curr_pct  = round(ai_top3[0]["curr"]/tc_curr*100,2) if ai_top3 and tc_curr else None
    a_top_prior_pct = round(ai_top3[0].get("prior",0)/tc_prior*100,2) if ai_top3 and tc_prior and ai_top3[0].get("prior") else None
    a_conc_total_curr  = sum(x["curr"] for x in ai_top3 if x["curr"])
    a_conc_total_prior = sum(x.get("prior",0) or 0 for x in ai_top3)
    a_conc_pct_curr    = round(a_conc_total_curr/tc_curr*100,2) if tc_curr else None
    a_conc_pct_prior   = round(a_conc_total_prior/tc_prior*100,2) if tc_prior else None

    a_commentary = (f"The top 3 biggest assets {'remain the same' if a_same_set else 'differ'} between the two periods. "
                    f"The combined concentration of the three largest assets {conc_word(a_conc_pct_curr, a_conc_pct_prior)}, "
                    f"moving from {a_conc_pct_prior:.2f}% to {a_conc_pct_curr:.2f}% of total assets. "
                    f"The largest single asset, {ai_top3[0]['label'] if ai_top3 else 'n/a'}, "
                    f"{'increased' if a_top_curr_pct and a_top_prior_pct and a_top_curr_pct>a_top_prior_pct else 'decreased'} "
                    f"its share from {a_top_prior_pct:.2f}% to {a_top_curr_pct:.2f}%.") if ai_top3 and tc_curr and tc_prior else ""

    a_takeaway = (f"Key takeaway: {ai_top3[0]['label'] if ai_top3 else 'The primary asset'} dominates the balance sheet at "
                  f"{a_top_curr_pct:.2f}% of total assets, reflecting the branch's core business focus. "
                  f"{'The top 3 concentration is above 80%, indicating high asset concentration risk.' if a_conc_pct_curr and a_conc_pct_curr>80 else 'Asset diversification is moderate across the top 3 items.'}") if ai_top3 and a_top_curr_pct else ""

    # ── Liability concentration commentary
    l_top3 = li_sorted[:3]
    li_prior = sorted([x for x in li if x.get("prior")], key=lambda x:x["prior"], reverse=True)[:3]
    l_labels_curr  = [x["label"] for x in l_top3]
    l_labels_prior = [x["label"] for x in li_prior]
    l_same_set = set(l_labels_curr) == set(l_labels_prior)

    l_conc_total_curr  = sum(x["curr"] for x in l_top3 if x["curr"])
    l_conc_total_prior = sum(x.get("prior",0) or 0 for x in l_top3)
    l_conc_pct_curr    = round(l_conc_total_curr/tl_curr*100,2) if tl_curr else None
    l_conc_pct_prior   = round(l_conc_total_prior/tl_prior*100,2) if tl_prior else None
    l_top_curr_pct     = round(l_top3[0]["curr"]/tl_curr*100,2) if l_top3 and tl_curr else None
    l_top_prior_pct    = round(l_top3[0].get("prior",0)/tl_prior*100,2) if l_top3 and tl_prior and l_top3[0].get("prior") else None

    # Biggest mover in liabilities
    l_movers = []
    for x in l_top3:
        if x["curr"] and x.get("prior") and tl_curr and tl_prior:
            diff = round(x["curr"]/tl_curr*100 - x["prior"]/tl_prior*100, 2)
            l_movers.append((x["label"], diff, x["curr"]-x["prior"]))
    l_movers.sort(key=lambda x:abs(x[1]),reverse=True)
    biggest_mover = l_movers[0] if l_movers else None

    l_commentary = (f"The top 3 biggest liabilities {'remain the same' if l_same_set else 'changed'} from the prior period. "
                    f"The combined concentration {conc_word(l_conc_pct_curr, l_conc_pct_prior)}, "
                    f"from {l_conc_pct_prior:.2f}% to {l_conc_pct_curr:.2f}% of total liabilities. "
                    + (f"The most notable shift was in {biggest_mover[0]}, whose share "
                       f"{'increased' if biggest_mover[1]>0 else 'decreased'} by {abs(biggest_mover[1]):.2f}pp, "
                       f"a change of approximately {fmt_n(abs(biggest_mover[2]))} {ul}."
                       if biggest_mover else "")) if l_top3 and tl_curr and tl_prior else ""

    l_takeaway = (f"Key takeaway: {l_top3[0]['label'] if l_top3 else 'The primary liability'} is the dominant funding source at "
                  f"{l_top_curr_pct:.2f}% of total liabilities. "
                  f"{'High liability concentration in the top 3 suggests potential funding concentration risk.' if l_conc_pct_curr and l_conc_pct_curr>70 else 'Liability funding is reasonably diversified across the top 3 items.'}") if l_top3 and l_top_curr_pct else ""

    # ── Summary
    prof_chg = pct_chg(prof[0],prof[1]) if prof else None
    summary = (f"{entity} reported profit after taxation of {fmt_n(prof[0])} {ul} for the period, "
               f"{'up' if prof_chg and prof_chg>0 else 'down'} {abs(prof_chg):.2f}% versus the prior period. "
               f"Total assets {'grew' if ta and ta[0]>ta[1] else 'contracted'} to {fmt_n(ta[0])} {ul}. "
               f"Liquidity ratios remain comfortably above regulatory minimums, and the branch maintains a "
               f"{'concentrated' if a_conc_pct_curr and a_conc_pct_curr>75 else 'diversified'} asset base "
               f"with {ai_top3[0]['label'] if ai_top3 else 'the primary asset'} as the dominant item.") if prof and ta else ""

    overall_takeaway = (f"The branch demonstrates {'strong' if prof_chg and prof_chg>0 else 'resilient'} financial performance with "
                        f"{'improving' if prof_chg and prof_chg>0 else 'stable'} profitability and robust liquidity buffers. "
                        f"The main risk to monitor is the concentration in {ai_top3[0]['label'] if ai_top3 else 'the largest asset class'}, "
                        f"which represents a dominant share of the balance sheet.") if prof and ai_top3 else ""

    today = datetime.date.today().strftime("%d %B %Y")

    # ── Build HTML ──────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{entity} — HKMA Disclosure Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'DM Sans',sans-serif;background:#fff;color:#111;font-size:10pt;line-height:1.6;
     max-width:780px;margin:0 auto;padding:40px 48px;}}
@media print{{body{{padding:20px 28px;}}}}
/* header */
.doc-header{{border-bottom:2px solid #111;padding-bottom:12px;margin-bottom:6px;
             display:flex;justify-content:space-between;align-items:flex-end;}}
.doc-title{{font-size:1.4rem;font-weight:700;letter-spacing:-.01em;line-height:1.1;}}
.doc-meta{{font-size:.68rem;color:#999;text-align:right;line-height:1.7;}}
.unit-tag{{display:inline-block;font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
           color:#E60028;border:1px solid #E60028;padding:1px 7px;margin:8px 0 18px;}}
.desc{{border-left:3px solid #E60028;padding:8px 12px;background:#fafafa;margin-bottom:24px;
       font-size:.8rem;color:#444;line-height:1.65;}}
/* section heading */
h2{{font-size:.62rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#555;
    border-bottom:1px solid #eee;padding-bottom:4px;margin-top:32px;margin-bottom:10px;}}
/* narrative */
.narrative{{font-size:.82rem;color:#333;line-height:1.7;margin-bottom:8px;}}
.takeaway{{font-size:.78rem;color:#555;font-style:italic;border-left:2px solid #E60028;
           padding-left:10px;margin:10px 0 16px;}}
/* table */
table{{width:100%;border-collapse:collapse;font-size:.78rem;margin:8px 0 18px;}}
thead tr{{border-bottom:2px solid #111;}}
th{{font-size:.58rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#999;
    padding:0 10px 7px;text-align:right;}}
th:first-child{{text-align:left;}}
td{{padding:7px 10px;border-bottom:1px solid #f0f0f0;color:#222;text-align:right;}}
td:first-child{{text-align:left;font-weight:500;color:#111;}}
tr:last-child td{{border-bottom:none;}}
.num{{font-variant-numeric:tabular-nums;}}
.pos{{color:#1a7a3a;font-weight:600;}}
.neg{{color:#E60028;font-weight:600;}}
.muted{{color:#bbb;}}
/* bullets */
.conc-section{{margin:10px 0;}}
.period-label{{font-size:.6rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
               color:#aaa;margin:14px 0 6px;}}
.bullet{{display:flex;align-items:baseline;gap:8px;padding:5px 0;border-bottom:1px solid #f5f5f5;font-size:.8rem;}}
.bullet:last-child{{border-bottom:none;}}
.arrow{{color:#E60028;font-weight:700;min-width:14px;}}
.bullet-name{{font-weight:600;color:#111;flex:1;}}
.bullet-pct{{font-weight:700;color:#111;min-width:90px;text-align:right;}}
.bullet-unit{{color:#bbb;font-size:.72rem;min-width:140px;text-align:right;}}
/* footer */
.doc-footer{{margin-top:48px;padding-top:12px;border-top:1px solid #eee;
             font-size:.62rem;color:#bbb;display:flex;justify-content:space-between;}}
.red{{color:#E60028;}}
hr{{border:none;border-top:1px solid #eee;margin:28px 0 0;}}
</style>
</head>
<body>

<div class="doc-header">
  <div class="doc-title">{entity}</div>
  <div class="doc-meta">
    HKMA Key Financial Information Disclosure<br>
    <span>{period}</span><br>
    <span style="color:#bbb">Generated {today}</span>
  </div>
</div>
<div class="unit-tag">Reported in {ul} &nbsp;·&nbsp; Snapshot in HKD billions</div>
{"<div class='desc'>" + desc + "</div>" if desc else ""}

<!-- LIQUIDITY -->
<h2>Liquidity Ratios</h2>

<p class="narrative"><strong>3-Month Liquidity Maintenance Ratio (LMR):</strong>
{"<span class='red'>" + (f"{lmr[0]:.2f}%" if lmr else "—") + "</span>" + " (current), " +
 (f"{lmr[1]:.2f}%" if lmr else "—") + " (prior)"}</p>
<p class="narrative">{lmr_text}</p>

<p class="narrative" style="margin-top:14px"><strong>3-Month Core Funding Ratio (CFR):</strong>
{"<span class='red'>" + (f"{cfr[0]:.2f}%" if cfr else "—") + "</span>" + " (current), " +
 (f"{cfr[1]:.2f}%" if cfr else "—") + " (prior)"}</p>
<p class="narrative">{cfr_text}</p>

{"<p class='narrative' style='margin-top:12px'>" + liq_summary + "</p>" if liq_summary else ""}

<!-- KEY FINANCIALS -->
<h2>Key Financials</h2>
<table>
  <thead><tr><th>Item</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
  <tbody>
    {kf_row("Profit after taxation", prof)}
    {kf_row("Total assets", ta)}
    {kf_row("Total liabilities", tl)}
    {kf_row("Specific provisions", spec)}
    {kf_row("Collective provisions", coll)}
    {kf_row("Total provisions", tot_prov)}
  </tbody>
</table>

<!-- ASSET CONCENTRATION -->
<h2>Asset Concentration</h2>

<div class="conc-section">
  <div class="period-label">Current period — top 3 assets</div>
  {conc_bullets(ai_top3, tc_curr, tc_prior, "current")}
</div>

<div class="conc-section" style="margin-top:14px">
  <div class="period-label">Prior period — top 3 assets</div>
  {conc_bullets(ai_prior[:3] if ai_prior else ai_top3, tc_curr, tc_prior, "prior", is_prior=True)}
</div>

<p class="narrative" style="margin-top:12px">{a_commentary}</p>
<p class="takeaway">{a_takeaway}</p>

<!-- LIABILITY CONCENTRATION -->
<h2>Liability Concentration</h2>

<div class="conc-section">
  <div class="period-label">Current period — top 3 liabilities</div>
  {conc_bullets(l_top3, tl_curr, tl_prior, "current")}
</div>

<div class="conc-section" style="margin-top:14px">
  <div class="period-label">Prior period — top 3 liabilities</div>
  {conc_bullets(li_prior[:3] if li_prior else l_top3, tl_curr, tl_prior, "prior", is_prior=True)}
</div>

<p class="narrative" style="margin-top:12px">{l_commentary}</p>
<p class="takeaway">{l_takeaway}</p>

<!-- SUMMARY -->
<hr>
<h2>Summary</h2>
<p class="narrative">{summary}</p>
<p class="takeaway">{overall_takeaway}</p>

<div class="doc-footer">
  <span>Source: HKMA Key Financial Information Disclosure Statement</span>
  <span>Generated by <span class="red">HKMA Disclosure Reader</span> · {today}</span>
</div>

</body>
</html>"""
    return html

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<h1>HKMA Financial Disclosure Reader</h1>", unsafe_allow_html=True)
uploaded = st.file_uploader("Upload HKMA Key Financial Information Disclosure PDF", type="pdf")

if not uploaded:
    st.markdown("""
    <div style="margin-top:40px;padding:40px;border:1px dashed #ddd;text-align:center;background:#fafafa">
      <div style="font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:#ccc;margin-bottom:6px;">
        Drop a disclosure PDF to begin
      </div>
      <div style="font-size:.7rem;color:#ddd;">
        Supports any HKMA-format bank disclosure — JPMorgan, CA-CIB, BNP Paribas, etc.
      </div>
    </div>
    """, unsafe_allow_html=True)

if uploaded:
    pdf_bytes = uploaded.read()
    with st.spinner("Extracting and generating report…"):
        d = run(pdf_bytes)

    ul   = d["unit_label"]
    mult = d["multiplier"]
    ta,tl= d["ta"],d["tl"]
    spec,coll = d["spec"],d["coll"]
    lmr,cfr   = d["lmr"],d["cfr"]
    prof      = d["profit"]
    ai,li     = d["asset_items"],d["liab_items"]
    entity    = d["entity"] or uploaded.name.replace(".pdf","").replace("_"," ").upper()
    desc      = d["desc"] or ""
    period    = d["period"] or ""

    tot_prov=None
    if spec and coll:
        c2=(spec[1]+coll[1]) if spec[1] and coll[1] else None
        tot_prov=(spec[0]+coll[0],c2)
    elif coll: tot_prov=coll
    elif spec: tot_prov=spec

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="pg-header">
      <div class="pg-bank">{entity}</div>
      <div class="pg-meta">HKMA Key Financial Disclosure<br><span>{period}</span></div>
    </div>
    <div class="unit-tag">Reported in {ul} &nbsp;·&nbsp; Snapshot figures in HKD billions</div>
    """, unsafe_allow_html=True)
    if desc:
        st.markdown(f'<div class="desc-block"><div class="desc-text">{desc}</div></div>',unsafe_allow_html=True)

    # ── Snapshot strip ───────────────────────────────────────────────────────
    def kpi_block(label,rv,rp,is_ratio=False):
        if rv is None: return ""
        display=f"{rv:.2f}%" if is_ratio else f"HKD {fmt_snapshot(rv,mult)}"
        if rp is not None:
            chg=round(rv-rp,2) if is_ratio else pct_chg(rv,rp)
            if chg is not None:
                sfx="pp" if is_ratio else "%"
                css="kpi-chg-pos" if chg>0 else "kpi-chg-neg"
                chg_html=f'<div class="{css}">{"+" if chg>0 else ""}{chg:.2f}{sfx} vs prior</div>'
            else: chg_html=""
        else: chg_html=""
        return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-val">{display}</div>{chg_html}</div>'

    kpis=""
    if ta:       kpis+=kpi_block("Total Assets",ta[0],ta[1])
    if prof:     kpis+=kpi_block("Profit after Tax",prof[0],prof[1])
    if lmr:      kpis+=kpi_block("Avg LMR",lmr[0],lmr[1],is_ratio=True)
    if cfr:      kpis+=kpi_block("Avg CFR",cfr[0],cfr[1],is_ratio=True)
    if tot_prov: kpis+=kpi_block("Total Provisions",tot_prov[0],tot_prov[1])
    if kpis:
        st.markdown(f'<div class="snapshot">{kpis}</div>',unsafe_allow_html=True)

    # ── Liquidity ────────────────────────────────────────────────────────────
    st.markdown("<h2>Liquidity</h2>",unsafe_allow_html=True)
    lpp=round(lmr[0]-lmr[1],2) if lmr else None
    cpp=round(cfr[0]-cfr[1],2) if cfr else None
    st.markdown(f"""
    <div class="ratio-grid">
      <div class="ratio-card">
        <div class="ratio-label">3-Month Average LMR</div>
        <div><span class="ratio-main">{f"{lmr[0]:.2f}%" if lmr else "—"}</span>
        <span class="ratio-prior">{f"prev {lmr[1]:.2f}%" if lmr else ""}</span></div>
        <div style="margin-top:6px">{pp_html(lpp)}</div>
      </div>
      <div class="ratio-card">
        <div class="ratio-label">3-Month Average CFR</div>
        <div><span class="ratio-main">{f"{cfr[0]:.2f}%" if cfr else "—"}</span>
        <span class="ratio-prior">{f"prev {cfr[1]:.2f}%" if cfr else ""}</span></div>
        <div style="margin-top:6px">{pp_html(cpp)}</div>
      </div>
    </div>""",unsafe_allow_html=True)

    # ── Key financials table ─────────────────────────────────────────────────
    st.markdown("<h2>Key Financials</h2>",unsafe_allow_html=True)
    kf_rows=[("Profit after taxation",prof),("Total assets",ta),("Total liabilities",tl),
             ("Specific provisions",spec),("Collective provisions",coll),("Total provisions",tot_prov)]
    rows_html=""
    for label,pair in kf_rows:
        if pair:
            c,p=pair[0],pair[1]
            rows_html+=f"<tr><td>{label}</td><td>{fmt_n(c)}</td><td>{fmt_n(p)}</td><td>{fmt_chg(pct_chg(c,p))}</td></tr>"
        else:
            rows_html+=f'<tr><td class="muted">{label}</td><td class="muted">—</td><td class="muted">—</td><td class="muted">—</td></tr>'
    st.markdown(f"""<table>
      <thead><tr><th>Metric</th><th>Current ({ul})</th><th>Prior ({ul})</th><th>Change</th></tr></thead>
      <tbody>{rows_html}</tbody></table>""",unsafe_allow_html=True)

    # ── Top 3 concentration ──────────────────────────────────────────────────
    def render_top3(items,total_pair,title):
        if not items or not total_pair: return
        tc,tp=total_pair[0],total_pair[1] if total_pair[1] else None
        valid=sorted([x for x in items if x["curr"] and x["curr"]>0],key=lambda x:x["curr"],reverse=True)[:3]
        st.markdown(f"<h2>{title} — Top 3</h2>",unsafe_allow_html=True)
        rows_h=""
        for i,x in enumerate(valid,1):
            pc=round(x["curr"]/tc*100,2) if tc else 0
            pp=round(x["prior"]/tp*100,2) if tp and x.get("prior") else None
            rows_h+=f"""<tr><td><span class="rank">{i}</span>{x['label']}</td>
              <td><b>{pc:.2f}%</b></td><td class="muted">{fmt_n(x['curr'])}</td>
              <td>{"<span class='muted'>—</span>" if pp is None else f"{pp:.2f}%"}</td>
              <td class="muted">{fmt_n(x.get('prior'))}</td></tr>"""
        st.markdown(f"""<table><thead><tr>
          <th style="text-align:left">Item</th><th>Curr %</th><th>Current ({ul})</th>
          <th>Prior %</th><th>Prior ({ul})</th></tr></thead>
          <tbody>{rows_h}</tbody></table>""",unsafe_allow_html=True)

    render_top3(ai,ta,"Asset Concentration")
    render_top3(li,tl,"Liability Concentration")

    # ── Full breakdown ────────────────────────────────────────────────────────
    st.markdown('<hr class="rule">',unsafe_allow_html=True)
    st.markdown("<h2>Full Balance Sheet Breakdown</h2>",unsafe_allow_html=True)

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
              <td>{"<span class='muted'>—</span>" if pc is None else f"<b>{pc:.2f}%</b>"}</td>
              <td class="muted">{fmt_n(x.get('prior'))}</td>
              <td>{"<span class='muted'>—</span>" if pp is None else f"{pp:.2f}%"}</td></tr>"""
        st.markdown(f"""<table><thead><tr>
          <th style="text-align:left">Item</th><th>Current ({ul})</th><th>% of Total</th>
          <th>Prior ({ul})</th><th>% of Total (Prior)</th></tr></thead>
          <tbody>{rows_h}</tbody></table>""",unsafe_allow_html=True)

    render_full(ai,ta,"Assets")
    render_full(li,tl,"Liabilities")

    # ── Downloads ─────────────────────────────────────────────────────────────
    st.markdown('<hr class="rule">',unsafe_allow_html=True)
    st.markdown("<h2>Export</h2>",unsafe_allow_html=True)

    report_html = generate_report_html(d, uploaded.name, ul, mult)
    base = uploaded.name.replace(".pdf","")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("↓  Download Report (HTML)",
                           data=report_html.encode("utf-8"),
                           file_name=f"{base}_report.html",
                           mime="text/html")
    with col2:
        export=[]
        for label,pair in kf_rows:
            if pair:
                export.append({"Section":"Key Financials","Item":label,
                                "Current":pair[0],"Prior":pair[1],"Change%":pct_chg(pair[0],pair[1])})
        if lmr: export.append({"Section":"Liquidity","Item":"Avg LMR (%)","Current":lmr[0],"Prior":lmr[1],"Change pp":lpp})
        if cfr:  export.append({"Section":"Liquidity","Item":"Avg CFR (%)","Current":cfr[0],"Prior":cfr[1],"Change pp":cpp})
        for x in sorted(ai,key=lambda x:x["curr"] or 0,reverse=True):
            pct=round(x["curr"]/ta[0]*100,2) if ta and x["curr"] else None
            export.append({"Section":"Assets","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
        for x in sorted(li,key=lambda x:x["curr"] or 0,reverse=True):
            pct=round(x["curr"]/tl[0]*100,2) if tl and x["curr"] else None
            export.append({"Section":"Liabilities","Item":x["label"],"Current":x["curr"],"Prior":x.get("prior"),"% of Total":pct})
        csv=pd.DataFrame(export).to_csv(index=False).encode("utf-8")
        st.download_button("↓  Download Raw Data (CSV)",data=csv,
                           file_name=f"{base}_metrics.csv",mime="text/csv")

    st.markdown("""<div style="font-size:.68rem;color:#aaa;margin-top:8px;">
      <b>To get a PDF:</b> open the downloaded HTML file in your browser → File → Print → Save as PDF
    </div>""",unsafe_allow_html=True)

    with st.expander("Debug — raw extracted lines"):
        st.text("\n".join(d["raw_lines"][:300]))
