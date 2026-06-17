import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import datetime

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

st.set_page_config(page_title="HKMA Disclosure Analyser", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Barlow:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Barlow Condensed', 'Arial Narrow', Arial, sans-serif !important;
    background: #FFFFFF !important;
    color: #1A1A1A !important;
}
.stApp { background: #FFFFFF !important; }
.block-container { max-width: 1120px; padding: 1.5rem 2rem 3rem; }
[data-testid="stFileUploader"] {
    border: 2px dashed #D0D0D0 !important;
    padding: 18px !important;
    background: #FAFAFA !important;
}
.pg-header { border-bottom: 3px solid #E60028; padding-bottom: 10px; margin-bottom: 24px; }
.pg-header h1 { font-size: 1.4rem; font-weight: 700; color: #1A1A1A; margin: 0 0 3px; }
.pg-header .sub { font-size: 0.79rem; color: #6B6B6B; margin: 0; }
.entity-banner { background: #F7F7F7; border-left: 5px solid #E60028; padding: 14px 20px; margin-bottom: 22px; }
.entity-banner h2 { font-size: 1.15rem; font-weight: 700; color: #1A1A1A; margin: 0 0 3px; text-transform: uppercase; letter-spacing: 0.5px; }
.entity-banner .meta { font-size: 0.78rem; color: #6B6B6B; }
.entity-banner .desc { font-size: 0.84rem; color: #1A1A1A; margin-top: 8px; line-height: 1.6; }
.sec-head { font-size: 0.6rem; font-weight: 700; letter-spacing: 2.2px; text-transform: uppercase;
    color: #E60028; border-bottom: 1px solid #E60028; padding-bottom: 5px; margin: 28px 0 14px; }
.kpi-card { flex: 1; min-width: 130px; background: #FFFFFF;
    border: 1px solid #E8E8E8; border-top: 3px solid #E60028; padding: 13px 16px; }
.kpi-label { font-size: 0.59rem; font-weight: 700; color: #6B6B6B;
    letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }
.kpi-val { font-size: 1.25rem; font-weight: 700; color: #1A1A1A; line-height: 1.2; }
.kpi-chg { font-size: 0.71rem; margin-top: 3px; }
.chg-pos { color: #E60028; font-weight: 700; }
.chg-neg { color: #1A1A1A; font-weight: 700; }
.neutral-box { background: #F7F7F7; border-left: 3px solid #CCCCCC;
    padding: 11px 16px; font-size: 0.84rem; color: #1A1A1A; margin: 8px 0 12px; line-height: 1.65; }
.analysis-box { background: #FFFFFF; border-top: 2px solid #E60028;
    border-bottom: 1px solid #E8E8E8; padding: 16px 20px; margin: 8px 0 18px; }
.analysis-box .ah { font-size: 0.59rem; font-weight: 700; color: #E60028;
    letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; }
.analysis-box p { font-size: 0.85rem; color: #1A1A1A; line-height: 1.75; margin: 0 0 9px; }
.analysis-box p:last-child { margin-bottom: 0; }
table.rep { width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-bottom: 4px; }
table.rep th { background: #1A1A1A; color: #FFFFFF; padding: 8px 12px; text-align: left;
    font-size: 0.63rem; font-weight: 700; letter-spacing: 0.9px; text-transform: uppercase; }
table.rep td { padding: 7px 12px; border-bottom: 1px solid #EEEEEE; color: #1A1A1A; }
table.rep tr:last-child td { border-bottom: none; }
table.rep tr:hover td { background: #F7F7F7; }
.nr { text-align: right !important; font-variant-numeric: tabular-nums; }
.brow td { font-weight: 700 !important; background: #F7F7F7 !important; }
.conc-wrap { background: #FFFFFF; border: 1px solid #E8E8E8; border-top: 2px solid #E60028; padding: 14px 18px; margin-bottom: 10px; }
.conc-head { font-size: 0.59rem; font-weight: 700; color: #6B6B6B;
    letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: 10px; }
.conc-item { display: flex; align-items: center; gap: 10px; padding: 6px 0;
    border-bottom: 1px solid #F2F2F2; font-size: 0.82rem; }
.conc-item:last-child { border-bottom: none; }
.ci-rank { color: #E60028; font-weight: 700; min-width: 18px; }
.ci-name { flex: 1; color: #1A1A1A; }
.ci-pct { font-weight: 700; color: #E60028; min-width: 52px; text-align: right; }
.ci-val { font-size: 0.74rem; color: #6B6B6B; min-width: 95px; text-align: right; }
.bar-wrap { background: #FFFFFF; border: 1px solid #E8E8E8; padding: 16px 18px; margin: 10px 0; }
.bar-title { font-size: 0.63rem; font-weight: 700; color: #6B6B6B;
    letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: 13px; }
.bar-row { margin-bottom: 9px; }
.bar-lrow { display: flex; justify-content: space-between; font-size: 0.75rem; color: #1A1A1A; margin-bottom: 3px; }
.bar-track { background: #F0F0F0; height: 10px; border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 2px; }
.lmr-block { background: #FFFFFF; border: 1px solid #E8E8E8; border-left: 4px solid #E60028; padding: 14px 18px; margin-bottom: 10px; }
.lmr-title { font-size: 0.63rem; font-weight: 700; letter-spacing: 1.6px; text-transform: uppercase; color: #E60028; margin-bottom: 8px; }
.lmr-vals { font-size: 1.05rem; font-weight: 700; color: #1A1A1A; margin-bottom: 8px; }
.lmr-bullet { padding-left: 0; margin: 0; }
.lmr-bullet li { list-style: none; font-size: 0.83rem; color: #1A1A1A; line-height: 1.7;
    margin-bottom: 3px; padding-left: 14px; position: relative; }
.lmr-bullet li::before { content: "--"; color: #E60028; font-weight: 700; margin-right: 6px; position: absolute; left: 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div class="pg-header">
  <h1>HKMA Financial Disclosure Analyser</h1>
  <p class="sub">Upload any HKMA Banking (Disclosure) Rules filing. Branches, incorporated banks, restricted licence banks.</p>
</div>
""", unsafe_allow_html=True)

CANONICAL = {
    r"cash and balances": "Cash and balances with banks",
    r"balances with banks$": "Balances with banks",
    r"balances with the monetary authority": "Balances with Monetary Authority",
    r"balances due from exchange fund|due from exchange fund|amount due from exchange fund": "Due from Exchange Fund",
    r"placements with banks": "Placements with banks",
    r"amounts? due from overseas offices|amount due from overseas": "Amounts due from overseas offices",
    r"trade bills": "Trade bills",
    r"certificates? of deposit held": "Certificates of deposit held",
    r"securities held for trading": "Securities held for trading",
    r"advances and other accounts": "Advances and other accounts",
    r"loans and receivables": "Loans and receivables",
    r"investment securities": "Investment securities",
    r"other investments": "Other investments",
    r"property.*plant.*equipment|property and equipment": "Property, plant and equipment",
    r"deposits and balances from central banks|from central banks": "Deposits from central banks",
    r"deposits and balances from banks|deposits from banks": "Deposits and balances from banks",
    r"balances due to exchange fund|amount due to exchange fund": "Balances due to Exchange Fund",
    r"demand deposits and current accounts|demand deposits": "Demand deposits and current accounts",
    r"saving deposits": "Saving deposits",
    r"time.*call.*notice deposits": "Time, call and notice deposits",
    r"amounts? due to overseas offices|amount due to overseas": "Amount due to overseas offices",
    r"certificates? of deposit issued": "Certificates of deposit issued",
    r"issued debt securities": "Issued debt securities",
    r"amount payable under repo": "Amount payable under repo",
    r"other accounts and provisions|other liabilities": "Other accounts / liabilities",
    r"^provisions$": "Provisions",
    r"deposits from customers": "Deposits from customers",
}

def canonicalize(raw):
    ll = raw.lower().strip()
    for pat, clean in CANONICAL.items():
        if re.search(pat, ll, re.IGNORECASE):
            return clean
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ", raw)
    s = re.sub(r"\s+"," ",s).strip()
    s = re.sub(r"[,\.\-\s]+$","",s).strip()
    return s[:70].rsplit(" ",1)[0].strip() if len(s)>70 else s

def clean_num(s):
    if not isinstance(s,str): return None
    s = s.strip().replace(",","").replace("\xa0","").replace(" ","")
    s = re.sub(r"HK\$|US\$|'000|港幣千元","",s).strip()
    if s in ("","--","-","Nil","nil","N/A"): return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[()$]","",s)
    try:
        v = float(s)
        return -v if neg else v
    except:
        return None

def trailing_nums(line):
    tokens = re.findall(r"\([\d,]+(?:\.\d+)?\)|[\d,]+(?:\.\d+)?", line)
    return [v for t in tokens for v in [clean_num(t)] if v is not None]

def raw_label(line):
    s = re.sub(r"\|","",line)
    s = re.sub(r"\*{1,2}","",s)
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",s)
    s = re.sub(r"(\s+[\(\-]?[\d,]+[\)]?)+\s*$","",s).strip()
    s = re.sub(r"[^a-zA-Z0-9\s,&'\-/\(\)\.:]+"," ",s)
    s = re.sub(r"\(see\s+part.*$","",s,flags=re.IGNORECASE).strip()
    s = re.sub(r",?\s*net\s+of\s+impairment\s+allowance","",s,flags=re.IGNORECASE).strip()
    return re.sub(r"\s+"," ",s).strip()

def detect_unit(lines):
    for line in lines[:150]:
        if re.search(r"in millions|millions of hk|million[s]? of hong kong",line,re.IGNORECASE):
            return "HKD millions", 1_000_000
        if re.search(r"HK\$\s*'?\s*0{3}",line,re.IGNORECASE):
            return "HKD thousands", 1_000
        if re.search(r"'000",line,re.IGNORECASE):
            return "HKD thousands", 1_000
    for line in lines:
        if re.search(r"HK\$\s*'?\s*0{3}|'000",line,re.IGNORECASE):
            return "HKD thousands", 1_000
        if re.search(r"in millions|millions of hk",line,re.IGNORECASE):
            return "HKD millions", 1_000_000
    return "HKD thousands", 1_000

def fmt_n(v): return "--" if v is None else f"{abs(v):,.0f}"
def pct_chg(c,p): return None if (c is None or p is None or p==0) else round((c-p)/abs(p)*100,2)
def fmt_chg(v):
    if v is None: return "--"
    cls = "chg-pos" if v>0 else "chg-neg"
    s = "+" if v>0 else ""
    return f'<span class="{cls}">{s}{v:.2f}%</span>'
def pp_html(v):
    if v is None: return "--"
    cls = "chg-pos" if v>0 else "chg-neg"
    s = "+" if v>0 else ""
    return f'<span class="{cls}">{s}{v:.2f}pp</span>'
def fmt_snapshot(v,mult):
    if v is None: return "--"
    hkd = abs(v)*mult
    if hkd>=1e12: return f"{hkd/1e12:.2f}T"
    if hkd>=1e9:  return f"{hkd/1e9:.1f}B"
    if hkd>=1e6:  return f"{hkd/1e6:.0f}M"
    return f"{hkd:,.0f}"

def is_noise(line):
    s = line.strip()
    if not s or len(s)<4: return True
    if re.match(r"^[^a-zA-Z0-9\-\(]",s): return True
    if re.match(r"^[A-Z]\d+\s*$",s): return True
    return False

def clean_for_match(line):
    s = re.sub(r"\|","",line)
    s = re.sub(r"\*{1,2}","",s)
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()

HARD_SKIP = re.compile(
    r"^total\s+(assets|liabilities)|^assets\s*$|^liabilities\s*$|"
    r"^equity\s+and\s+liabilities\s*$|^less:\s*impairment|"
    r"^impairment\s+allowances\s+for|^provision\s+for\s+impaired|"
    r"^balance\s+sheet|^section\s+[a-z]|^\d+\s*$|^page\s|"
    r"^reserves?\s*$|^[-_=\s]+$|^note\s|^figures\s+in|^unaudited|"
    r"^international\s+claims|^non-bank|^currency\s+risk|^remuneration|"
    r"^group\s+consolidated|^declaration\s+of\s+compliance",
    re.IGNORECASE)
INCOME_SKIP = re.compile(
    r"profit\s+before\s+tax|profit\s+after\s+tax|net\s+profit\s*$|"
    r"interest\s+income|interest\s+expense|operating\s+income|"
    r"operating\s+expense|taxation\s+charge|tax\s+expense|"
    r"reversal\s+of\s+impairment|net\s+write|net\s+fees|"
    r"net\s+interest|gains\s+less\s+losses|total\s+operating",
    re.IGNORECASE)
DED_SKIP    = re.compile(r"^\s*[-]\s+(collective|specific)\b", re.IGNORECASE)
HEADER_SKIP = re.compile(
    r"^natixis\s*$|^corporate\s+and\s+investment\s+banking\s*$|"
    r"^groupe\s+bpce\s*$|^kpmg",
    re.IGNORECASE)

def extract_pages(pdf_bytes):
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i,page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            rows  = []
            for tbl in (page.extract_tables() or []):
                for row in tbl:
                    rows.append([c.strip() if isinstance(c,str) else (c or "") for c in row])
            pages.append((i, lines, rows))
    return pages

def ocr_all(pdf_bytes):
    if not OCR_AVAILABLE: return []
    imgs = convert_from_bytes(pdf_bytes, dpi=200)
    out  = []
    for img in imgs:
        t = pytesseract.image_to_string(img)
        out += [l.strip() for l in t.splitlines() if l.strip()]
    return out

def parse_bs(lines, section="assets"):
    items  = []
    in_sec = False
    if section == "assets":
        s_pat = re.compile(r"^\**assets\**\s*$|^\**assets\**\s+as\s+at", re.IGNORECASE)
        e_pat = re.compile(r"total\s+assets", re.IGNORECASE)
    else:
        s_pat = re.compile(r"^\**liabilities\**\s*$|equity\s+and\s+liabilities", re.IGNORECASE)
        e_pat = re.compile(r"total\s+liabilities", re.IGNORECASE)
    for line in lines:
        s  = line.strip()
        if not s: continue
        cm = clean_for_match(s)
        if s_pat.match(cm):    in_sec = True; continue
        if not in_sec:         continue
        if e_pat.search(cm):   in_sec = False; continue
        if HARD_SKIP.search(cm) or INCOME_SKIP.search(cm) or DED_SKIP.match(cm): continue
        if HEADER_SKIP.match(cm): continue
        if is_noise(cm): continue
        nums  = trailing_nums(s)
        if not nums: continue
        curr  = nums[-2] if len(nums) >= 2 else nums[-1]
        prior = nums[-1] if len(nums) >= 2 else None
        if curr == 0 and (prior is None or prior == 0): continue
        rl    = raw_label(s)
        label = canonicalize(rl)
        if not label or len(label) < 2: continue
        if re.match(r"^[\d,.() \-\s]+$", label): continue
        if any(x["label"] == label for x in items): continue
        items.append({"label": label, "curr": abs(curr),
                      "prior": abs(prior) if prior is not None else None})
    return items

def find_two(lines, pattern):
    for i,line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            nums = trailing_nums(line)
            if len(nums) >= 2: return nums[-2], nums[-1]
            for j in range(i+1, min(i+4,len(lines))):
                nums += trailing_nums(lines[j])
                if len(nums) >= 2: return nums[-2], nums[-1]
    return None

def get_provisions(lines):
    spec, coll = None, None
    for line in lines:
        ll = line.lower()
        if re.search(r"collective\s+(impairment|provision)|[-]\s*collective\b", ll):
            nums = trailing_nums(line)
            if nums and coll is None:
                coll = (abs(nums[-2] if len(nums)>=2 else nums[-1]),
                        abs(nums[-1]) if len(nums)>=2 else None)
        if re.search(r"specific\s+(impairment|provision)|individual\s+impairment|[-]\s*specific\b", ll):
            nums = trailing_nums(line)
            if nums and spec is None:
                spec = (abs(nums[-2] if len(nums)>=2 else nums[-1]),
                        abs(nums[-1]) if len(nums)>=2 else None)
    return {"spec": spec, "coll": coll}

def get_lmr_cfr(lines, pdf_bytes):
    lmr = find_two(lines, r"average\s+(liquidity\s+maintenance|lmr)|average\s+lmr")
    cfr = find_two(lines, r"average\s+(core\s+funding|cfr)|average\s+cfr")
    if not (lmr and cfr):
        ol = ocr_all(pdf_bytes)
        if not lmr: lmr = find_two(ol, r"average.*lmr|lmr.*%")
        if not cfr: cfr = find_two(ol, r"average.*cfr|cfr.*%")
    return lmr, cfr

def get_entity_name(lines):
    NON_NAME = re.compile(
        r"^(natixis\s+corporate|corporate\s+and\s+investment|groupe\s+bpce|kpmg|"
        r"financial\s+information\s+disclosure|financial\s+statements|"
        r"incorporated\s+in|unaudited|figures\s+in|for\s+identification|"
        r"investment\s+banking|and\s+investment)", re.IGNORECASE)
    for line in lines[:60]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean = re.sub(r"\(.*?\)","",clean).strip()
        clean = re.sub(r"\s+"," ",clean).strip()
        if re.search(r"hong\s+kong\s+branch", clean, re.IGNORECASE):
            before = re.sub(r"hong\s+kong\s+branch.*$","",clean,flags=re.IGNORECASE).strip()
            if len(before.split()) >= 1: return clean[:100]
    for line in lines[:20]:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean = re.sub(r"\(.*?\)","",clean).strip()
        clean = re.sub(r"\s+"," ",clean).strip()
        if not clean or len(clean)<4: continue
        if re.match(r"^[\d\s\-/]+$",clean): continue
        if NON_NAME.match(clean): continue
        if len(clean.split())>=1 and clean[0].isupper(): return clean[:100]
    return "Unknown Bank"

def get_branch_description(lines):
    in_para, para_lines = False, []
    section_headers = re.compile(
        r"^(additional\s+profit|profit\s+and\s+loss|balance\s+sheet|off-balance|"
        r"supplementary|section\s+[a-z]|contents|for\s+the\s+(year|half)|remuneration|"
        r"liquidity|currency\s+risk|international\s+claims|mainland|group\s+consolidated)",
        re.IGNORECASE)
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        clean = re.sub(r"[^a-zA-Z0-9\s,&\.\-/()\!:@'\"]+","",clean).strip()
        clean = re.sub(r"\s+"," ",clean).strip()
        if re.search(r"branch activities|branch information", clean, re.IGNORECASE):
            in_para = True; continue
        if in_para:
            if not clean or len(clean)<5: continue
            if section_headers.match(clean) or re.match(r"^[-_=]+$",clean): break
            if re.match(r"^[\d\s]+$",clean): continue
            para_lines.append(clean)
            if len(" ".join(para_lines))>350: break
    desc = " ".join(para_lines)
    if not desc:
        for line in lines:
            clean = re.sub(r"[\u4e00-\u9fff]+","",line).strip()
            if re.search(r"we have pleasure|incorporated in|registered under|a branch of",
                         clean,re.IGNORECASE) and len(clean.split())>8:
                desc = clean; break
    if len(desc)>350: desc = desc[:350].rsplit(" ",1)[0]+"..."
    return desc

def get_period(lines):
    for line in lines:
        clean = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+","",line).strip()
        if re.search(r"(year|period|half.year)\s+ended|for the year|as at|as of",clean,re.IGNORECASE):
            if re.search(r"\d{4}",clean):
                return re.sub(r"\s+"," ",clean).strip()[:80]
    return ""

def get_profit_loss(lines):
    r = find_two(lines, r"profit\s+after\s+tax(?:ation)?|net\s+profit\s*$|除稅後溢利")
    if r: return r
    return find_two(lines, r"profit\s+before\s+tax(?:ation)?")

def run(pdf_bytes):
    pages = extract_pages(pdf_bytes)
    all_lines = []
    for _,lines,_ in pages: all_lines += lines
    bs_lines = []
    for _,lines,_ in pages[:6]: bs_lines += lines
    ul, mult  = detect_unit(bs_lines)
    ta        = find_two(all_lines, r"total\s+assets|總資產")
    tl        = find_two(all_lines, r"total\s+liabilities|總負債")
    profit    = get_profit_loss(all_lines)
    prov      = get_provisions(all_lines)
    lmr, cfr  = get_lmr_cfr(all_lines, pdf_bytes)
    ai        = parse_bs(all_lines, "assets")
    li        = parse_bs(all_lines, "liabilities")
    entity    = get_entity_name(all_lines)
    desc      = get_branch_description(all_lines)
    period    = get_period(all_lines)
    return {"unit_label":ul,"multiplier":mult,"ta":ta,"tl":tl,"profit":profit,
            "spec":prov["spec"],"coll":prov["coll"],"lmr":lmr,"cfr":cfr,
            "asset_items":ai,"liab_items":li,"entity":entity,"desc":desc,
            "period":period,"raw_lines":all_lines}

# ── ANALYSIS ENGINE ────────────────────────────────────────────────────────────

def build_analysis(d, mult, ul):
    ta     = d["ta"];   tl    = d["tl"]
    profit = d["profit"]
    spec   = d["spec"]; coll  = d["coll"]
    lmr    = d["lmr"];  cfr   = d["cfr"]
    ai = sorted([x for x in d["asset_items"] if x["curr"]], key=lambda x:x["curr"], reverse=True)
    li = sorted([x for x in d["liab_items"]  if x["curr"]], key=lambda x:x["curr"], reverse=True)
    entity = d["entity"] or "This institution"

    tc_c = ta[0] if ta else None;  tc_p = ta[1] if ta else None
    tl_c = tl[0] if tl else None;  tl_p = tl[1] if tl else None
    pr_c = profit[0] if profit else None; pr_p = profit[1] if profit else None

    roa        = round(pr_c/tc_c*100,3) if (pr_c and tc_c) else None
    roa_p      = round(pr_p/tc_p*100,3) if (pr_p and tc_p) else None
    profit_chg = pct_chg(pr_c,pr_p)
    asset_chg  = pct_chg(tc_c,tc_p)

    tot_prov_c = tot_prov_p = None
    if spec and coll:
        tot_prov_c = (spec[0] or 0)+(coll[0] or 0)
        tot_prov_p = ((spec[1] or 0)+(coll[1] or 0)) if (spec[1] is not None or coll[1] is not None) else None
    elif spec:  tot_prov_c = spec[0]; tot_prov_p = spec[1]
    elif coll:  tot_prov_c = coll[0]; tot_prov_p = coll[1]
    prov_chg = pct_chg(tot_prov_c, tot_prov_p)

    out = {}

    # LMR
    if lmr:
        lc,lp = lmr[0],lmr[1]
        diff  = round(lc-lp,2) if lp else None
        direction = "increased" if (diff or 0)>0 else ("decreased" if (diff or 0)<0 else "remained stable")
        if lc>=300:   level="exceptionally high"
        elif lc>=150: level="very strong"
        elif lc>=75:  level="solid"
        elif lc>=35:  level="adequate"
        else:         level="tight, approaching the 25% regulatory floor"
        top_a = ai[0]["label"] if ai else ""
        if lc>=150 and "overseas" in top_a.lower():
            reason="high intragroup asset placements qualifying as HQLA, reflecting this branch's role as a group liquidity vehicle"
        elif lc>=150:
            reason="a structurally large stock of liquid assets relative to short-term liabilities, consistent with conservative treasury positioning"
        else:
            reason="normal balance sheet management within internal limits"
        if diff and abs(diff)>20:
            cause=("a significant shift in the short-term funding mix -- either a reduction in wholesale borrowings "
                   "or an increase in liquid asset holdings. Executives should confirm whether this reflects deliberate "
                   "repositioning or a timing effect around the reporting date.")
        elif diff and diff>0:  cause="modest accumulation of HQLA or a small reduction in short-term liabilities"
        elif diff and diff<0:  cause="deployment of liquid assets into higher-yielding instruments or loans, or an increase in short-term wholesale funding"
        else:                  cause="stable balance sheet composition with no material change in liquidity drivers"
        out.update(lmr_c=lc,lmr_p=lp,lmr_diff=diff,lmr_direction=direction,
                   lmr_level=level,lmr_reason=reason,lmr_cause=cause)
    else:
        out.update(lmr_c=None,lmr_p=None,lmr_diff=None,lmr_direction=None,
                   lmr_level=None,lmr_reason=None,lmr_cause=None)

    # CFR
    if cfr:
        cc,cp = cfr[0],cfr[1]
        cdiff = round(cc-cp,2) if cp else None
        cdir  = "decreased" if (cdiff or 0)<0 else ("increased" if (cdiff or 0)>0 else "remained stable")
        if cc>=200:
            cmean=(f"stable funding covers illiquid assets by {cc/100:.1f}x, providing strong structural resilience. "
                   "The branch is not dependent on short-term wholesale markets to fund its balance sheet.")
        elif cc>=100:
            cmean=("stable funding just covers illiquid assets. The branch meets structural requirements "
                   "but has limited buffer against deposit outflows or funding market disruption.")
        else:
            cmean=("stable funding does not fully cover illiquid assets -- a structural maturity mismatch. "
                   "The branch relies on short-term funding for longer-term assets, which should be monitored closely.")
        out.update(cfr_c=cc,cfr_p=cp,cfr_diff=cdiff,cfr_dir=cdir,cfr_meaning=cmean)
    else:
        out.update(cfr_c=None,cfr_p=None,cfr_diff=None,cfr_dir=None,cfr_meaning=None)

    # Asset concentration
    if ai and tc_c:
        top_name = ai[0]["label"]
        top_pct  = ai[0]["curr"]/tc_c*100
        if "overseas" in top_name.lower():
            a_analysis=(f"The dominant position of {top_name} ({top_pct:.1f}% of total assets) confirms "
                        f"{entity} operates primarily as an intragroup booking and funding conduit. "
                        "The real credit exposure does not reside on this balance sheet -- it sits at the parent group level. "
                        "Executives reviewing this filing should focus on parent group health, not local provisions. "
                        "The HKMA supervises this structure under its overseas branch framework, which requires the parent "
                        "to stand behind all local obligations.")
        elif "loan" in top_name.lower() or "advance" in top_name.lower():
            llr=round(tot_prov_c/ai[0]["curr"]*100,2) if (tot_prov_c and ai[0]["curr"]) else None
            a_analysis=(f"A loan-dominant balance sheet ({top_pct:.1f}% in {top_name}) signals this branch "
                        "generates revenue primarily from credit intermediation. Credit risk sits with local "
                        "and external borrowers -- local provisions are the primary risk barometer."
                        +(f" The loan loss reserve stands at {llr:.2f}% of the dominant loan category, "
                          f"{'which is thin and worth monitoring closely' if llr and llr<1 else 'a reasonable buffer for current conditions'}."
                          if llr else "")
                        +" Executives should watch the NPL trajectory and provision coverage ratio as leading indicators.")
        elif "investment" in top_name.lower() or "securities" in top_name.lower():
            a_analysis=(f"An investment-led balance sheet ({top_pct:.1f}% in {top_name}) means this branch "
                        "operates as a treasury and market-making vehicle. Duration mismatch and mark-to-market "
                        "volatility on the securities portfolio are the primary executive risk concerns.")
        else:
            a_analysis=(f"The balance sheet is reasonably diversified. The largest position ({top_name} at {top_pct:.1f}%) "
                        "does not indicate a structural concentration. Risk is distributed across business lines, "
                        "reducing idiosyncratic exposure while potentially reflecting a less focused business model.")

        prior_ai = sorted([x for x in ai if x.get("prior")],key=lambda x:x["prior"],reverse=True)
        curr_top3  = {x["label"] for x in ai[:3]}
        prior_top3 = {x["label"] for x in prior_ai[:3]}
        same_comp  = curr_top3 == prior_top3
        top3_curr_conc  = sum(x["curr"] for x in ai[:3])/tc_c*100 if tc_c else 0
        top3_prior_conc = sum(x["prior"] for x in prior_ai[:3])/tc_p*100 if (prior_ai and tc_p) else None

        if same_comp:
            if top3_prior_conc:
                diff_c = top3_curr_conc-top3_prior_conc
                trend  = "increased" if diff_c>0 else "decreased" if diff_c<0 else "was unchanged"
                comp_sent=(f"The top 3 biggest assets remain the same between the two periods. "
                           f"The concentration of the three biggest assets {trend}, "
                           f"with the combined share moving from {top3_prior_conc:.1f}% to {top3_curr_conc:.1f}% of total assets.")
            else:
                comp_sent="The top 3 biggest assets remain the same between the two periods."
        else:
            added   = curr_top3-prior_top3
            removed = prior_top3-curr_top3
            comp_sent=("The top 3 biggest assets changed between periods. "
                       +(f"Newly entering the top 3: {', '.join(added)}. " if added else "")
                       +(f"No longer in top 3: {', '.join(removed)}. " if removed else "")
                       +f"Combined concentration of current top 3: {top3_curr_conc:.1f}%.")
        out.update(a_analysis=a_analysis,a_comp_sent=comp_sent,
                   ai_sorted=ai,prior_ai=prior_ai,
                   top3_curr_conc=top3_curr_conc,top3_prior_conc=top3_prior_conc)
    else:
        out.update(a_analysis=None,a_comp_sent=None,ai_sorted=[],prior_ai=[],
                   top3_curr_conc=None,top3_prior_conc=None)

    # Liability concentration
    if li and tl_c:
        top_l     = li[0]["label"]
        top_l_pct = li[0]["curr"]/tl_c*100
        if "customer" in top_l.lower() or ("deposit" in top_l.lower() and "bank" not in top_l.lower()):
            l_analysis=(f"Customer deposits ({top_l_pct:.1f}% of liabilities) are the primary funding source. "
                        "This is the most stable funding type but carries behavioural and repricing risk. "
                        "A retail deposit franchise protects net interest margin in a rising rate environment "
                        "but creates vulnerability if rates fall or deposit competition intensifies."
                        +(f" The LMR of {out['lmr_c']:.1f}% provides adequate short-term coverage." if out.get("lmr_c") else ""))
        elif "overseas" in top_l.lower() or ("bank" in top_l.lower() and top_l_pct>30):
            l_analysis=(f"Wholesale and intragroup funding ({top_l_pct:.1f}% in {top_l}) dominates the liability structure. "
                        "This is the most fragile funding type -- it can be withdrawn at short notice and is the first "
                        "channel through which parent group stress transmits to this balance sheet. "
                        "Executives should assess rollover risk and parent credit standing. The CFR is the most important ratio here."
                        +(f" A CFR of {out['cfr_c']:.1f}% {'indicates adequate structural funding cover' if (out.get('cfr_c') or 0)>=100 else 'indicates a structural gap requiring monitoring'}." if out.get("cfr_c") else ""))
        else:
            l_analysis=(f"The funding base is reasonably diversified with {top_l} at {top_l_pct:.1f}% as the largest source. "
                        "No single liability category creates an overwhelming concentration risk. "
                        "The maturity profile and repricing structure of the largest components should be reviewed alongside the liquidity disclosures.")

        prior_li = sorted([x for x in li if x.get("prior")],key=lambda x:x["prior"],reverse=True)
        curr_top3_l  = {x["label"] for x in li[:3]}
        prior_top3_l = {x["label"] for x in prior_li[:3]}
        same_l = curr_top3_l == prior_top3_l
        movers = []
        for x in li:
            if x.get("prior") and tl_c and tl_p:
                cp2 = x["curr"]/tl_c*100; pp2 = x["prior"]/tl_p*100
                movers.append((x["label"],cp2-pp2,cp2,pp2))
        movers.sort(key=lambda x:abs(x[1]),reverse=True)
        top3l_curr  = sum(x["curr"] for x in li[:3])/tl_c*100 if tl_c else 0
        top3l_prior = sum(x["prior"] for x in prior_li[:3])/tl_p*100 if (prior_li and tl_p) else None

        if same_l:
            if top3l_prior:
                ld = top3l_curr-top3l_prior
                lt = "rose" if ld>0 else "fell" if ld<0 else "was unchanged"
                l_comp_sent=(f"The top 3 biggest liabilities remain the same between the two periods, "
                             f"though the concentration {lt} from {top3l_prior:.1f}% to {top3l_curr:.1f}%. ")
            else:
                l_comp_sent="The top 3 biggest liabilities remain the same between the two periods. "
        else:
            added_l = curr_top3_l-prior_top3_l
            l_comp_sent=(f"The top 3 biggest liabilities changed between periods."
                         +(f" Newly entering: {', '.join(added_l)}." if added_l else "")
                         +f" Combined concentration of current top 3: {top3l_curr:.1f}%. ")
        if movers:
            mv   = movers[0]
            sign = "rose" if mv[1]>0 else "fell"
            l_comp_sent+=(f"From the prior period, the concentration of {mv[0]} {sign} by around {abs(mv[1]):.1f}pp "
                          f"(from {mv[3]:.1f}% to {mv[2]:.1f}%).")
        out.update(l_analysis=l_analysis,l_comp_sent=l_comp_sent,li_sorted=li,prior_li=prior_li)
    else:
        out.update(l_analysis=None,l_comp_sent=None,li_sorted=[],prior_li=[])

    # Credit risk sentence
    if tot_prov_c is not None:
        direction = "rose" if (prov_chg or 0)>0 else "fell"
        pct_abs   = abs(prov_chg) if prov_chg else 0
        if spec and coll:
            drv="a mix of specific and collective provisions"
            impl=("both identified borrower-level deterioration and broader portfolio stress" if (prov_chg or 0)>0
                  else "releases across both impaired-credit and model-driven collective allowances")
        elif spec:
            drv="specific provisions"
            impl=("more identified credit risk on named counterparties" if (prov_chg or 0)>0
                  else "specific provisions being released as impaired credits resolved")
        elif coll:
            drv="collective provisions"
            impl=("a broader portfolio-level expected-loss build" if (prov_chg or 0)>0
                  else "improving expected-loss estimates across the portfolio")
        else:
            drv="provisions"; impl="higher identified credit risk" if (prov_chg or 0)>0 else "improving credit quality"

        dom = out.get("ai_sorted",[None])[0]["label"] if out.get("ai_sorted") else ""
        if "overseas" in dom.lower():
            risk_loc="the parent group and its global counterparty network"
            risk_ctx=("Local provisions are largely symbolic relative to the intragroup asset base. "
                      "The real credit risk sits on the consolidated parent balance sheet.")
        elif "loan" in dom.lower() or "advance" in dom.lower():
            risk_loc="external borrowers in the local loan book"
            risk_ctx=("The provisions trajectory is the key leading indicator, typically leading NPL recognition by one to two quarters.")
        else:
            risk_loc="a distributed mix of local and intragroup counterparties"
            risk_ctx="Credit risk is diversified; no single exposure dominates the risk profile."

        out["credit_sent"]=(
            f"Provisions {direction} {pct_abs:.1f}%, driven by {drv}, implying {impl}. "
            f"The dominant asset is {dom if dom else 'not clearly identifiable'}, "
            f"so credit risk sits primarily with {risk_loc}. {risk_ctx}"
            if prov_chg is not None else
            f"Provisions are reported but no prior-period comparison is available. "
            f"Credit risk sits primarily with {risk_loc}. {risk_ctx}"
        )
    else:
        out["credit_sent"] = None

    # Executive analysis
    positives, concerns = [], []
    if out.get("lmr_c") and out["lmr_c"]>=100:
        positives.append(f"LMR of {out['lmr_c']:.1f}% ({out.get('lmr_level','strong')}) -- well above the 25% regulatory floor")
    elif out.get("lmr_c") and out["lmr_c"]<50:
        concerns.append(f"LMR of {out['lmr_c']:.1f}% is approaching the regulatory minimum; short-term liquidity is thin")
    if out.get("cfr_c") and out["cfr_c"]>=200:
        positives.append(f"CFR of {out['cfr_c']:.1f}% -- structural funding covers illiquid assets {out['cfr_c']/100:.1f}x")
    elif out.get("cfr_c") and out["cfr_c"]<100:
        concerns.append("CFR below 100% indicates a structural maturity mismatch -- stable funding does not cover illiquid assets")
    if roa and roa>0.5:
        positives.append(f"ROA of {roa:.2f}% is above average for a branch-format institution")
    elif roa is not None and roa<=0:
        concerns.append(f"Loss-making in the current period (ROA: {roa:.2f}%)")
    if profit_chg and profit_chg>15:
        positives.append(f"Profit growth of {profit_chg:.1f}% signals improving revenue or provision releases")
    elif profit_chg and profit_chg<-25:
        concerns.append(f"Profit fell {abs(profit_chg):.1f}% -- verify whether provision-driven, revenue compression, or one-off")
    if prov_chg and prov_chg>30:
        concerns.append(f"Provisions rose {prov_chg:.1f}% -- significant credit quality deterioration signal")
    elif prov_chg and prov_chg<-20:
        positives.append(f"Provision releases of {abs(prov_chg):.1f}% indicate improving credit quality")
    if asset_chg and asset_chg>15:
        positives.append(f"Balance sheet grew {asset_chg:.1f}% -- expansion in business volumes")
    elif asset_chg and asset_chg<-10:
        concerns.append(f"Total assets contracted {abs(asset_chg):.1f}% -- monitor for strategic deleveraging vs funding withdrawal")

    if positives and not concerns:    tone="presents a fundamentally sound financial profile."
    elif positives and concerns:      tone="shows a mixed but broadly stable financial profile."
    elif concerns:                    tone="presents several indicators requiring executive attention."
    else:                             tone="requires further qualitative context to assess."

    exec_paras = []
    p1 = f"{entity} {tone}"
    if positives: p1 += " Key strengths: " + "; ".join(positives) + "."
    if concerns:  p1 += " Areas requiring attention: " + "; ".join(concerns) + "."
    exec_paras.append(p1)

    if out.get("lmr_c") and out.get("cfr_c"):
        pos_liq = "adequate headroom above regulatory thresholds on both short-term and structural liquidity" if (out["lmr_c"]>=50 and out["cfr_c"]>=100) else "a tighter liquidity profile that warrants monitoring"
        exec_paras.append(
            f"On liquidity: the LMR of {out['lmr_c']:.1f}% reflects {out['lmr_reason']}. "
            f"The movement was most likely caused by {out['lmr_cause']}. "
            f"Structurally, {out['cfr_meaning']} "
            f"Together, these ratios indicate {entity} has {pos_liq}.")
    if out.get("a_analysis"):
        exec_paras.append(f"On balance sheet composition: {out['a_analysis']}")
    if out.get("credit_sent"):
        exec_paras.append(f"On credit quality: {out['credit_sent']}")
    if profit_chg is not None:
        if abs(profit_chg)>50:
            exec_paras.append(f"Profitability: profit {'surged' if profit_chg>0 else 'collapsed'} {abs(profit_chg):.0f}% -- verify whether driven by operating leverage, provision releases, or one-off items.")
        elif abs(profit_chg)>15:
            exec_paras.append(f"Profitability: profit {'grew' if profit_chg>0 else 'fell'} {abs(profit_chg):.0f}%. Monitor the provisions trend as the leading credit quality indicator.")
        else:
            exec_paras.append(f"Profitability: profit is broadly stable ({profit_chg:+.1f}%). Earnings quality depends on the provisions trajectory and revenue mix.")

    actions = []
    if any("provision" in c.lower() for c in concerns):
        actions.append("request a detailed provision breakdown by sector and counterparty")
    if any("cfr" in c.lower() for c in concerns):
        actions.append("review the maturity ladder and confirm funding rollover commitments for the next 6-12 months")
    if any("lmr" in c.lower() for c in concerns):
        actions.append("monitor daily liquidity positions against the internal LMR trigger level")
    if any("profit" in c.lower() or "loss" in c.lower() for c in concerns):
        actions.append("obtain a prior-to-current period profit bridge to isolate non-recurring items")
    if actions:
        exec_paras.append("Recommended executive actions: " + "; ".join(actions) + ".")

    exec_html = "".join(f"<p>{p}</p>" for p in exec_paras)

    out.update(exec_html=exec_html,roa=roa,roa_p=roa_p,profit_chg=profit_chg,
               tc_c=tc_c,tc_p=tc_p,tl_c=tl_c,tl_p=tl_p,pr_c=pr_c,pr_p=pr_p,
               spec_c=spec[0] if spec else None, spec_p=spec[1] if spec else None,
               coll_c=coll[0] if coll else None, coll_p=coll[1] if coll else None,
               tot_prov_c=tot_prov_c,tot_prov_p=tot_prov_p,prov_chg=prov_chg)
    return out

# ── RENDER HELPERS ─────────────────────────────────────────────────────────────

BAR_COLORS = ["#E60028","#C0001F","#1A1A1A","#555555","#888888","#AAAAAA","#C8C8C8","#E0E0E0"]

def render_bar(items, total, title):
    if not items or not total:
        st.markdown('<div class="neutral-box">Breakdown not available for this filing.</div>', unsafe_allow_html=True)
        return
    top = sorted(items, key=lambda x: x["curr"], reverse=True)[:7]
    rest_val = sum(x["curr"] for x in items if x not in top)
    segments = [(x["label"][:34], round(x["curr"]/total*100, 2), BAR_COLORS[i % len(BAR_COLORS)])
                for i, x in enumerate(top)]
    if rest_val > 0:
        segments.append(("Other", round(rest_val/total*100, 2), "#E8E8E8"))
    segs = "".join(
        f'<div style="width:{pct:.2f}%;background:{col};height:100%;display:inline-block;'
        f'vertical-align:top;box-sizing:border-box;" title="{lbl}: {pct:.1f}%"></div>'
        for lbl, pct, col in segments
    )
    legend = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin:3px 12px 3px 0;font-size:0.72rem;">'
        f'<span style="display:inline-block;width:11px;height:11px;border-radius:2px;background:{col};flex-shrink:0;"></span>'
        f'<span style="color:#1A1A1A;">{lbl}</span>'
        f'<span style="font-weight:700;color:{col};">{pct:.1f}%</span></span>'
        for lbl, pct, col in segments
    )
    html = (
        '<div class="bar-wrap">'
        f'<div class="bar-title">{title}</div>'
        '<div style="width:100%;height:24px;border-radius:3px;overflow:hidden;'
        'display:flex;margin-bottom:13px;border:1px solid #E8E8E8;">'
        f'{segs}</div>'
        f'<div style="line-height:1.9;">{legend}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

def conc_block(items, total, mult, ul, label):
    if not items or not total:
        st.markdown('<div class="neutral-box">Not extractable from this filing.</div>', unsafe_allow_html=True); return
    rows = ""
    for i,x in enumerate(items[:3],1):
        pct = x["curr"]/total*100 if total else 0
        rows += (f'<div class="conc-item">'
                 f'<span class="ci-rank">{i}</span>'
                 f'<span class="ci-name">{x["label"]}</span>'
                 f'<span class="ci-pct">{pct:.2f}%</span>'
                 f'<span class="ci-val">{ul} {fmt_snapshot(x["curr"],mult)}</span>'
                 f'</div>')
    st.markdown(f'<div class="conc-wrap"><div class="conc-head">{label}</div>{rows}</div>', unsafe_allow_html=True)

def conc_block_prior(items, total_p, mult, ul, label):
    if not items or not total_p:
        st.markdown('<div class="neutral-box">Prior period data not available.</div>', unsafe_allow_html=True); return
    prior_sorted = sorted([x for x in items if x.get("prior")], key=lambda x:x["prior"], reverse=True)[:3]
    if not prior_sorted:
        st.markdown('<div class="neutral-box">Prior period data not available.</div>', unsafe_allow_html=True); return
    rows = ""
    for i,x in enumerate(prior_sorted,1):
        pct = x["prior"]/total_p*100 if total_p else 0
        rows += (f'<div class="conc-item">'
                 f'<span class="ci-rank">{i}</span>'
                 f'<span class="ci-name">{x["label"]}</span>'
                 f'<span class="ci-pct">{pct:.2f}%</span>'
                 f'<span class="ci-val">{ul} {fmt_snapshot(x["prior"],mult)}</span>'
                 f'</div>')
    st.markdown(f'<div class="conc-wrap"><div class="conc-head">{label}</div>{rows}</div>', unsafe_allow_html=True)

def trow(label, c, p, bold=False):
    chg = pct_chg(c,p)
    cls = ' class="brow"' if bold else ""
    return (f"<tr{cls}><td>{label}</td>"
            f'<td class="nr">{fmt_n(c)}</td>'
            f'<td class="nr">{fmt_n(p)}</td>'
            f'<td class="nr">{fmt_chg(chg)}</td></tr>')

def prow(label, c, p):
    d  = None if (c is None or p is None) else c-p
    cs = f"{c:.2f}%" if c is not None else "--"
    ps = f"{p:.2f}%" if p is not None else "--"
    ds = pp_html(d) if d is not None else "--"
    return (f"<tr><td>{label}</td>"
            f'<td class="nr">{cs}</td>'
            f'<td class="nr">{ps}</td>'
            f'<td class="nr">{ds}</td></tr>')

def full_table_rows(items, tc, tp):
    rows = ""
    for x in items:
        c = x["curr"]; p = x.get("prior")
        pct_c = f"{c/tc*100:.1f}%" if (c and tc) else "--"
        pct_p = f"{p/tp*100:.1f}%" if (p and tp) else "--"
        rows += (f"<tr><td>{x['label']}</td>"
                 f'<td class="nr">{pct_c}</td>'
                 f'<td class="nr">{fmt_n(c)}</td>'
                 f'<td class="nr">{pct_p}</td>'
                 f'<td class="nr">{fmt_n(p)}</td></tr>')
    return rows or "<tr><td colspan='5'>No items extracted.</td></tr>"

# ── HTML REPORT BUILDER ────────────────────────────────────────────────────────

def build_html_report(d, ana, filename, ul, mult):
    entity = d["entity"] or filename
    period = d["period"] or ""
    desc   = d["desc"]   or ""
    ai     = ana.get("ai_sorted", [])
    li     = ana.get("li_sorted", [])
    tc_c   = ana["tc_c"]; tc_p = ana["tc_p"]
    tl_c   = ana["tl_c"]; tl_p = ana["tl_p"]
    lc=ana.get("lmr_c"); lp=ana.get("lmr_p"); ld=ana.get("lmr_diff")
    cc=ana.get("cfr_c"); cp=ana.get("cfr_p"); cd=ana.get("cfr_diff")

    def conc_li(items, total, key="curr"):
        out = ""
        tot = tc_c if key=="curr" else tc_p
        for i,x in enumerate(items[:3],1):
            v = x.get(key)
            if v is None: continue
            pct = v/tot*100 if tot else 0
            out += f"<li><strong>{i}. {x['label']}</strong> -- {pct:.2f}% of total assets | {ul} {fmt_snapshot(v,mult)}</li>"
        return out or "<li>Not extractable.</li>"

    def conc_li_l(items, total, key="curr"):
        out = ""
        tot = tl_c if key=="curr" else tl_p
        for i,x in enumerate(items[:3],1):
            v = x.get(key)
            if v is None: continue
            pct = v/tot*100 if tot else 0
            out += f"<li><strong>{i}. {x['label']}</strong> -- {pct:.2f}% of total liabilities | {ul} {fmt_snapshot(v,mult)}</li>"
        return out or "<li>Not extractable.</li>"

    def full_tbl(items, tc, tp):
        rows=""
        for x in items:
            c=x["curr"]; p=x.get("prior")
            pc=f"{c/tc*100:.1f}%" if (c and tc) else "--"
            pp2=f"{p/tp*100:.1f}%" if (p and tp) else "--"
            chg=pct_chg(c,p); chg_s=f"{chg:+.1f}%" if chg is not None else "--"
            rows+=(f"<tr><td>{x['label']}</td>"
                   f"<td class='r'>{pc}</td><td class='r'>{fmt_n(c)}</td>"
                   f"<td class='r'>{pp2}</td><td class='r'>{fmt_n(p)}</td>"
                   f"<td class='r'>{chg_s}</td></tr>")
        return rows or "<tr><td colspan='6'>No data.</td></tr>"

    ft=""
    for lbl,cv,pv,bold in [
        ("Profit after taxation",   ana["pr_c"],       ana["pr_p"],       True),
        ("Return on assets (%)",    ana["roa"],        ana["roa_p"],      False),
        ("Total assets",            tc_c,              tc_p,              True),
        ("Total liabilities",       tl_c,              tl_p,              False),
        ("Specific provisions",     ana["spec_c"],     ana["spec_p"],     False),
        ("Collective provisions",   ana["coll_c"],     ana["coll_p"],     False),
        ("Total provisions",        ana["tot_prov_c"], ana["tot_prov_p"], True),
    ]:
        chg=pct_chg(cv,pv); chg_s=f"{chg:+.1f}%" if chg is not None else "--"
        vc=f"{cv:.4f}" if "%" in lbl and cv else fmt_n(cv)
        vp=f"{pv:.4f}" if "%" in lbl and pv else fmt_n(pv)
        b="<strong>" if bold else ""; be="</strong>" if bold else ""
        ft+=(f"<tr><td>{b}{lbl}{be}</td><td class='r'>{b}{vc}{be}</td>"
             f"<td class='r'>{b}{vp}{be}</td><td class='r'>{chg_s}</td></tr>")

    lmr_html=""
    if lc:
        lp_s=f"{lp:.2f}%" if lp else "--"; ld_s=f"{ld:+.2f}pp" if ld is not None else "--"
        lmr_html=(f"<p><strong>3-Month Average LMR: {lc:.2f}% (current) / {lp_s} (prior)</strong></p>"
                  f"<ul>"
                  f"<li>The LMR {ana['lmr_direction']} from {lp_s} to {lc:.2f}% ({ld_s})</li>"
                  f"<li>{entity} holds enough liquid assets to cover approximately {lc:.0f}% of liabilities due within one month</li>"
                  f"<li>Reason for change: {ana['lmr_reason']}</li>"
                  f"<li>Most likely caused by: {ana['lmr_cause']}</li>"
                  f"<li>The LMR remains {'well above' if lc>=50 else 'above'} the 25% regulatory minimum</li>"
                  f"</ul>")
    cfr_html=""
    if cc:
        cp_s=f"{cp:.2f}%" if cp else "--"; cd_s=f"{cd:+.2f}pp" if cd is not None else "--"
        cfr_html=(f"<p><strong>3-Month Average CFR: {cc:.2f}% (current) / {cp_s} (prior)</strong></p>"
                  f"<ul>"
                  f"<li>The CFR {ana['cfr_dir']}, going from {cp_s} to {cc:.2f}% ({cd_s})</li>"
                  f"<li>{ana['cfr_meaning']}</li>"
                  f"<li>CFR remains {'well above' if cc>=100 else 'above'} the 75% regulatory minimum</li>"
                  f"</ul>")
    liq_summary=""
    if lc and cc:
        liq_summary=(f"<p>In terms of liquidity, {entity} is "
                     f"{'above average on both ratios' if (lc>=100 and cc>=100) else 'within regulatory bounds on both ratios'} "
                     f"and is able to cover over {lc:.0f}% of its one-month liabilities.</p>")

    prior_ai = sorted([x for x in ai if x.get("prior")], key=lambda x:x["prior"], reverse=True)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>{entity} -- HKMA Disclosure Analysis</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Barlow:wght@300;400;500;600;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif;background:#fff;color:#1A1A1A;font-size:13px;line-height:1.65;}}
.page{{max-width:900px;margin:30px auto;padding:0 24px 48px;}}
h1{{font-size:20px;font-weight:700;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.5px;}}
.meta{{font-size:11px;color:#6B6B6B;margin-bottom:6px;}}
.banner{{border-left:5px solid #E60028;padding:14px 18px;background:#F7F7F7;margin-bottom:22px;}}
.desc{{font-size:12.5px;margin-top:8px;color:#1A1A1A;}}
.sec{{font-size:9px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;
      color:#E60028;border-bottom:1px solid #E60028;padding-bottom:4px;margin:28px 0 14px;}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px;}}
th{{background:#1A1A1A;color:#fff;padding:7px 10px;text-align:left;font-size:9px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;}}
td{{padding:6px 10px;border-bottom:1px solid #eee;}}
tr:last-child td{{border-bottom:none;}}
tr:hover td{{background:#F7F7F7;}}
.r{{text-align:right;font-family:'Courier New',monospace;}}
.box{{background:#F7F7F7;border-left:3px solid #E60028;padding:12px 16px;margin:10px 0 14px;font-size:12.5px;line-height:1.7;}}
.box ul{{padding-left:18px;margin:6px 0 0;}}.box li{{margin-bottom:4px;}}
.abox{{background:#fff;border-top:2px solid #E60028;border-bottom:1px solid #eee;padding:14px 18px;margin:8px 0 18px;font-size:12.5px;line-height:1.75;}}
.abox .ah{{font-size:9px;font-weight:700;color:#E60028;letter-spacing:2px;text-transform:uppercase;margin-bottom:9px;}}
.abox p{{margin-bottom:8px;}}.abox p:last-child{{margin-bottom:0;}}
.abox ul{{padding-left:18px;margin-bottom:8px;}}.abox li{{margin-bottom:4px;}}
@media print{{body{{font-size:11px;}}.page{{margin:0;padding:20px;}}table{{break-inside:avoid;}}.abox{{break-inside:avoid;}}}}
</style></head><body><div class="page">
<div class="banner">
  <h1>{entity}</h1>
  <div class="meta">{period} | Figures in {ul}</div>
  {"<div class='desc'>"+desc+"</div>" if desc else ""}
</div>
<div class="sec">Main Takeaway -- Executive Assessment</div>
<div class="abox"><div class="ah">What Executives Need to Know</div>
{ana.get("exec_html","<p>Analysis not available.</p>")}
</div>
<div class="sec">3-Month Liquidity Ratios</div>
<div class="box">{lmr_html}{cfr_html}{liq_summary}</div>
<div class="sec">Financial Summary</div>
<table><thead><tr>
<th style="width:36%">Item</th>
<th class="r" style="width:20%">'25 ({ul})</th>
<th class="r" style="width:20%">'24 ({ul})</th>
<th class="r" style="width:24%">Change</th>
</tr></thead><tbody>{ft}</tbody></table>
<div class="sec">Asset Quality and Credit Risk</div>
<div class="abox"><div class="ah">Credit Risk Assessment</div>
<p>{ana.get("credit_sent","Provision data not found in this filing.")}</p></div>
<div class="sec">Asset Concentration -- Current Period</div>
<div class="box"><ul>{conc_li(ai,tc_c,"curr")}</ul></div>
<div class="sec">Asset Concentration -- Prior Period</div>
<div class="box"><ul>{conc_li(prior_ai,tc_p,"prior")}</ul></div>
<div class="abox"><div class="ah">Asset Concentration Trend</div>
<p>{ana.get("a_comp_sent","")}</p></div>
<div class="sec">Full Asset Concentration Table</div>
<table><thead><tr>
<th>Item</th><th class="r">% Curr</th><th class="r">Curr</th>
<th class="r">% Prior</th><th class="r">Prior</th><th class="r">Change</th>
</tr></thead><tbody>{full_tbl(ai,tc_c,tc_p)}</tbody></table>
<div class="abox"><div class="ah">Analysis -- What This Tells You</div>
<p>{ana.get("a_analysis","Not available.")}</p></div>
<div class="sec">Liability Concentration -- Current Period</div>
<div class="box"><ul>{conc_li_l(li,tl_c,"curr")}</ul></div>
<div class="sec">Liability Concentration -- Prior Period</div>
<div class="box"><ul>{conc_li_l(li,tl_p,"prior")}</ul></div>
<div class="abox"><div class="ah">Liability Concentration Trend</div>
<p>{ana.get("l_comp_sent","")}</p></div>
<div class="sec">Full Liability Concentration Table</div>
<table><thead><tr>
<th>Item</th><th class="r">% Curr</th><th class="r">Curr</th>
<th class="r">% Prior</th><th class="r">Prior</th><th class="r">Change</th>
</tr></thead><tbody>{full_tbl(li,tl_c,tl_p)}</tbody></table>
<div class="abox"><div class="ah">Analysis -- What This Tells You</div>
<p>{ana.get("l_analysis","Not available.")}</p></div>
</div></body></html>"""

# ── MAIN RENDER ────────────────────────────────────────────────────────────────

def render(d, filename, ul, mult):
    ana    = build_analysis(d, mult, ul)
    entity = d["entity"] or filename
    period = d["period"] or ""
    desc   = d["desc"]   or ""
    ai     = ana.get("ai_sorted", [])
    li     = ana.get("li_sorted", [])
    tc_c   = ana["tc_c"]; tc_p = ana["tc_p"]
    tl_c   = ana["tl_c"]; tl_p = ana["tl_p"]
    lc=ana.get("lmr_c"); lp=ana.get("lmr_p"); ld=ana.get("lmr_diff")
    cc=ana.get("cfr_c"); cp=ana.get("cfr_p"); cd=ana.get("cfr_diff")

    # Entity banner
    desc_html = f'<div class="desc">{desc}</div>' if desc else ""
    st.markdown(f'<div class="entity-banner"><h2>{entity}</h2>'
                f'<div class="meta">{period} &nbsp;|&nbsp; Figures in {ul}</div>'
                f'{desc_html}</div>', unsafe_allow_html=True)

    # Main takeaway
    st.markdown('<div class="sec-head">Main Takeaway</div>', unsafe_allow_html=True)
    if ana.get("exec_html"):
        st.markdown(f'<div class="analysis-box"><div class="ah">Executive Assessment</div>'
                    f'{ana["exec_html"]}</div>', unsafe_allow_html=True)

    # KPI strip
    st.markdown('<div class="sec-head">Key Metrics</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    def kpi(col, label, val, chg_val, is_pp=False):
        with col:
            v_str = f"{val:.2f}%" if (is_pp and val is not None) else (fmt_n(val) if val is not None else "--")
            b = ""
            if chg_val is not None:
                cls = "chg-pos" if chg_val>0 else "chg-neg"
                s   = "+" if chg_val>0 else ""
                sfx = "pp" if is_pp else "%"
                b   = f'<span class="{cls}">{s}{chg_val:.2f}{sfx}</span>'
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                        f'<div class="kpi-val">{v_str}</div>'
                        f'<div class="kpi-chg">{b}&nbsp;</div></div>', unsafe_allow_html=True)
    kpi(c1,"Total Assets",    ana["tc_c"],      pct_chg(ana["tc_c"],ana["tc_p"]))
    kpi(c2,"Profit / (Loss)", ana["pr_c"],      pct_chg(ana["pr_c"],ana["pr_p"]))
    kpi(c3,"Avg LMR",         lc,               ld, is_pp=True)
    kpi(c4,"Avg CFR",         cc,               cd, is_pp=True)

    # Liquidity
    st.markdown('<div class="sec-head">Liquidity Ratios</div>', unsafe_allow_html=True)
    if lc is not None:
        lp_s = f"{lp:.2f}%" if lp else "--"
        ld_s = f"{ld:+.2f}pp" if ld is not None else "--"
        st.markdown(f'<div class="lmr-block"><div class="lmr-title">3-Month Average Liquidity Maintenance Ratio (LMR)</div>'
                    f'<div class="lmr-vals">{lc:.2f}% (current) / {lp_s} (prior) | {ld_s}</div>'
                    f'<ul class="lmr-bullet">'
                    f'<li>The LMR {ana["lmr_direction"]} from {lp_s} to {lc:.2f}%</li>'
                    f'<li>{entity} holds enough liquid assets to cover approximately {lc:.0f}% of liabilities due within one month</li>'
                    f'<li>Reason for change: {ana["lmr_reason"]}</li>'
                    f'<li>Most likely caused by: {ana["lmr_cause"]}</li>'
                    f'<li>The LMR remains {"well above" if lc>=50 else "above"} the 25% regulatory minimum</li>'
                    f'</ul></div>', unsafe_allow_html=True)
    if cc is not None:
        cp_s = f"{cp:.2f}%" if cp else "--"
        cd_s = f"{cd:+.2f}pp" if cd is not None else "--"
        st.markdown(f'<div class="lmr-block"><div class="lmr-title">3-Month Average Core Funding Ratio (CFR)</div>'
                    f'<div class="lmr-vals">{cc:.2f}% (current) / {cp_s} (prior) | {cd_s}</div>'
                    f'<ul class="lmr-bullet">'
                    f'<li>The CFR {ana["cfr_dir"]}, going from {cp_s} to {cc:.2f}%</li>'
                    f'<li>{ana["cfr_meaning"]}</li>'
                    f'<li>CFR remains {"well above" if cc>=100 else "above"} the 75% regulatory minimum</li>'
                    f'</ul></div>', unsafe_allow_html=True)
    if lc and cc:
        liq_s = (f"In terms of liquidity, {entity} is "
                 f"{'above average on both ratios' if (lc>=100 and cc>=100) else 'within regulatory bounds on both ratios'} "
                 f"and is able to cover over {lc:.0f}% of its one-month liabilities.")
        st.markdown(f'<div class="neutral-box">{liq_s}</div>', unsafe_allow_html=True)

    # Financial summary
    st.markdown('<div class="sec-head">Financial Summary</div>', unsafe_allow_html=True)
    rows = (trow("Profit after taxation",  ana["pr_c"],       ana["pr_p"],       bold=True)
          + trow("Return on assets (%)",    ana["roa"],        ana["roa_p"])
          + trow("Total assets",            tc_c,              tc_p,              bold=True)
          + trow("Total liabilities",       tl_c,              tl_p)
          + trow("Specific provisions",     ana["spec_c"],     ana["spec_p"])
          + trow("Collective provisions",   ana["coll_c"],     ana["coll_p"])
          + trow("Total provisions",        ana["tot_prov_c"], ana["tot_prov_p"], bold=True))
    st.markdown(f'<table class="rep"><thead><tr>'
                f'<th style="width:36%">Item</th>'
                f'<th class="nr" style="width:20%">\'25 ({ul})</th>'
                f'<th class="nr" style="width:20%">\'24 ({ul})</th>'
                f'<th class="nr" style="width:24%">Change</th>'
                f'</tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
    if lc or cc:
        rr = prow("Avg LMR",lc,lp) + prow("Avg CFR",cc,cp)
        st.markdown(f'<table class="rep" style="margin-top:10px;"><thead><tr>'
                    f'<th style="width:40%">Ratio</th>'
                    f'<th class="nr">Current</th><th class="nr">Prior</th><th class="nr">Change</th>'
                    f'</tr></thead><tbody>{rr}</tbody></table>', unsafe_allow_html=True)

    # Credit risk
    st.markdown('<div class="sec-head">Asset Quality and Credit Risk</div>', unsafe_allow_html=True)
    if ana.get("credit_sent"):
        st.markdown(f'<div class="analysis-box"><div class="ah">Credit Risk Assessment</div>'
                    f'<p>{ana["credit_sent"]}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="neutral-box">Provision data not found in this filing.</div>', unsafe_allow_html=True)

    # Asset concentration
    st.markdown('<div class="sec-head">Asset Concentration</div>', unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1: conc_block(ai,  tc_c, mult, ul, f"Current -- {period[:22] if period else 'Current period'}")
    with col2: conc_block_prior(ai, tc_p, mult, ul, "Prior period")
    if ai and tc_c: render_bar(ai, tc_c, "Asset Composition (Current Period)")
    if ana.get("a_comp_sent"):
        st.markdown(f'<div class="neutral-box">{ana["a_comp_sent"]}</div>', unsafe_allow_html=True)
    with st.expander("Full asset breakdown table"):
        st.markdown(f'<table class="rep"><thead><tr>'
                    f'<th>Item</th><th class="nr">% Curr</th><th class="nr">Curr ({ul})</th>'
                    f'<th class="nr">% Prior</th><th class="nr">Prior ({ul})</th>'
                    f'</tr></thead><tbody>{full_table_rows(ai,tc_c,tc_p)}</tbody></table>', unsafe_allow_html=True)
    if ana.get("a_analysis"):
        st.markdown(f'<div class="analysis-box"><div class="ah">Analysis -- What This Tells You</div>'
                    f'<p>{ana["a_analysis"]}</p></div>', unsafe_allow_html=True)

    # Liability concentration
    st.markdown('<div class="sec-head">Liability Concentration</div>', unsafe_allow_html=True)
    col3,col4 = st.columns(2)
    with col3: conc_block(li,  tl_c, mult, ul, f"Current -- {period[:22] if period else 'Current period'}")
    with col4: conc_block_prior(li, tl_p, mult, ul, "Prior period")
    if li and tl_c: render_bar(li, tl_c, "Liability Composition (Current Period)")
    if ana.get("l_comp_sent"):
        st.markdown(f'<div class="neutral-box">{ana["l_comp_sent"]}</div>', unsafe_allow_html=True)
    with st.expander("Full liability breakdown table"):
        st.markdown(f'<table class="rep"><thead><tr>'
                    f'<th>Item</th><th class="nr">% Curr</th><th class="nr">Curr ({ul})</th>'
                    f'<th class="nr">% Prior</th><th class="nr">Prior ({ul})</th>'
                    f'</tr></thead><tbody>{full_table_rows(li,tl_c,tl_p)}</tbody></table>', unsafe_allow_html=True)
    if ana.get("l_analysis"):
        st.markdown(f'<div class="analysis-box"><div class="ah">Analysis -- What This Tells You</div>'
                    f'<p>{ana["l_analysis"]}</p></div>', unsafe_allow_html=True)

    # Export
    st.markdown('<div class="sec-head">Export Report</div>', unsafe_allow_html=True)
    html_report = build_html_report(d, ana, filename, ul, mult)
    safe        = re.sub(r"[^a-zA-Z0-9_\-]","_", entity)[:40]
    import csv as _csv
    buf = io.StringIO()
    w   = _csv.writer(buf)
    w.writerow(["Metric",f"Current ({ul})",f"Prior ({ul})","Change"])
    for lbl,cv,pv in [
        ("Total Assets",tc_c,tc_p),("Total Liabilities",tl_c,tl_p),
        ("Profit after Tax",ana["pr_c"],ana["pr_p"]),("ROA (%)",ana["roa"],ana["roa_p"]),
        ("Specific Provisions",ana["spec_c"],ana["spec_p"]),
        ("Collective Provisions",ana["coll_c"],ana["coll_p"]),
        ("Total Provisions",ana["tot_prov_c"],ana["tot_prov_p"]),
        ("LMR (%)",lc,lp),("CFR (%)",cc,cp),
    ]:
        chg=pct_chg(cv,pv)
        w.writerow([lbl,fmt_n(cv),fmt_n(pv),f"{chg:+.1f}%" if chg is not None else "--"])
    ca,cb = st.columns(2)
    with ca:
        st.download_button("Download HTML Report  (open in browser, Ctrl+P to save as PDF)",
                           data=html_report, file_name=f"{safe}_report.html", mime="text/html")
    with cb:
        st.download_button("Download CSV Data",
                           data=buf.getvalue(), file_name=f"{safe}_data.csv", mime="text/csv")

# ── UPLOAD ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload HKMA Banking Disclosure PDF", type=["pdf"],
                             help="Supports all standard HKMA Banking (Disclosure) Rules filings")
if uploaded:
    pdf_bytes = uploaded.read()
    with st.spinner("Parsing PDF and building analysis..."):
        try:
            d    = run(pdf_bytes)
            ul   = d["unit_label"]
            mult = d["multiplier"]
            render(d, uploaded.name, ul, mult)
        except Exception as e:
            st.error(f"Could not process this PDF. Error: {e}")
            st.info("This filing may use a non-standard layout. Try a different PDF or contact support.")
else:
    st.markdown('<div class="neutral-box">Upload a PDF above to generate the analysis report.</div>',
                unsafe_allow_html=True)
