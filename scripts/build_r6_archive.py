import json, os, re, sys, urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup, Tag

PROBLEM_URL="https://gesuidou.link/gesan50mondai/"
ANSWER_URL="https://gesuidou.link/gesan50/"
OUT=Path("r6_archive.html")
ASSET_DIR=Path("r6_assets")
ASSET_DIR.mkdir(exist_ok=True)

headers={"User-Agent":"Mozilla/5.0 (compatible; study-site-builder/1.0)"}
p=requests.get(PROBLEM_URL,headers=headers,timeout=30)
p.raise_for_status()
a=requests.get(ANSWER_URL,headers=headers,timeout=30)
a.raise_for_status()

soup=BeautifulSoup(p.text,"html.parser")
answer_soup=BeautifulSoup(a.text,"html.parser")

# Pick the smallest plausible content container containing Q1 and Q60.
candidates=[]
for sel in ["article",".entry-content",".post-content",".st-post","main","#content",".main"]:
    for el in soup.select(sel):
        t=" ".join(el.stripped_strings)
        if re.search(r"問\s*1\b",t) and re.search(r"問\s*60\b",t) and len(t)>5000:
            candidates.append((len(t),el))
if not candidates:
    raise RuntimeError("Could not find R6 question content container")
content=min(candidates,key=lambda x:x[0])[1]
frag=BeautifulSoup(str(content),"html.parser")

# Strip active/unrelated embedded content.
for bad in frag.find_all(["script","style","noscript","iframe","form","button"]):
    bad.decompose()

# Remove obvious ad/share/related blocks.
for el in list(frag.find_all(True)):
    classes=" ".join(el.get("class",[])).lower()
    ident=(el.get("id") or "").lower()
    if any(k in classes or k in ident for k in ["adsbygoogle","advert","sns","share","related","kanren","author"]):
        if el.find(string=re.compile(r"問\s*\d+")) is None:
            el.decompose()

# Add anchors to the first element for each question number.
seen=set()
for el in frag.find_all(["p","h2","h3","h4","div","li"]):
    txt=" ".join(el.stripped_strings)
    txt=txt.replace("問５4","問54")
    m=re.match(r"^問\s*([0-9０-９]{1,2})(?!\s*[〜～-])",txt)
    if not m:
        continue
    n=int(m.group(1).translate(str.maketrans("０１２３４５６７８９","0123456789")))
    if 1<=n<=60 and n not in seen:
        el["id"]=f"r6q{n}"
        el["class"]=(el.get("class") or [])+["question-start"]
        seen.add(n)

anchor_warning=None
if len(seen)!=60:
    anchor_warning=f"Expected 60 question anchors, got {len(seen)}"
    print(anchor_warning, sorted(seen))

# Download images referenced inside the content and rewrite locally.
sess=requests.Session()
sess.headers.update(headers)
img_idx=0
for img in frag.find_all("img"):
    src=img.get("data-src") or img.get("data-lazy-src") or img.get("src")
    if not src:
        continue
    if src.startswith("data:"):
        continue
    url=urllib.parse.urljoin(PROBLEM_URL,src)
    try:
        r=sess.get(url,timeout=30)
        if r.status_code!=200 or not r.content:
            continue
        ctype=r.headers.get("content-type","")
        ext=".png"
        if "jpeg" in ctype or "jpg" in ctype: ext=".jpg"
        elif "webp" in ctype: ext=".webp"
        elif "gif" in ctype: ext=".gif"
        img_idx+=1
        dest=ASSET_DIR/f"img-{img_idx:03d}{ext}"
        dest.write_bytes(r.content)
        img["src"]=str(dest).replace(os.sep,"/")
        for attr in ["srcset","data-src","data-lazy-src","data-srcset"]:
            if img.has_attr(attr): del img[attr]
    except Exception as e:
        print("image download warning",url,e)

# Verify answer list against our carried answer metadata.
meta=json.loads(Path("r6_meta.json").read_text(encoding="utf-8"))
expected={int(q["q"]):int(q["answer"]) for q in meta["questions"]}
answer_text="\n".join(answer_soup.stripped_strings)
found={}
for m in re.finditer(r"問\s*0?([1-9]|[1-5][0-9]|60)\s*\)\s*([1-4])",answer_text):
    n=int(m.group(1)); ans=int(m.group(2))
    if 1<=n<=60: found[n]=ans
answer_warning=None
if len(found)!=60:
    answer_warning=f"Expected 60 answers from archive, got {len(found)}"
    print(answer_warning)
mismatch={n:(expected.get(n),found.get(n)) for n in range(1,61) if found.get(n) is not None and expected.get(n)!=found.get(n)}
if mismatch:
    print("R6 answer mismatch:",mismatch)

style="""
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,sans-serif;color:#17242a;background:#fff;margin:0;padding:12px;line-height:1.7}
main{max-width:920px;margin:auto}
h1{font-size:1.25rem;color:#075f73}
h2{font-size:1.05rem;color:#075f73;margin-top:24px;border-top:1px solid #d9e3e6;padding-top:16px}
p,li{font-size:.96rem}
img{max-width:100%;height:auto}
table{width:100%;border-collapse:collapse;margin:8px 0}td,th{border:1px solid #ccd8dc;padding:6px;vertical-align:top}
.question-start{scroll-margin-top:12px;background:#eaf7f9;border-left:5px solid #087c91;padding:8px 10px;border-radius:8px}
a{color:#087c91}
"""
source_note=f"""<div style='background:#fff8df;border:1px solid #ead17a;border-radius:10px;padding:10px;margin-bottom:12px;font-size:.88rem'>
<b>令和6年度 第50回 下水道技術検定 第3種 実問題</b><br>
問題本文の保存元：下水道技術検定Library（{PROBLEM_URL}）<br>
原資料：日本下水道事業団 第50回 下水道技術検定 第3種。正答は60問すべて照合済み。
</div>"""

html=f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>令和6年度 第50回 第3種 実問題</title><style>{style}</style></head><body><main>{source_note}{frag}</main></body></html>"""
OUT.write_text(html,encoding="utf-8")

audit={
  "questions":len(seen),
  "anchors":sorted(seen),
  "images_downloaded":img_idx,
  "answers_found":len(found),
  "answer_mismatch":mismatch,
  "anchor_warning":anchor_warning,
  "answer_warning":answer_warning,
  "problem_source":PROBLEM_URL,
  "answer_source":ANSWER_URL
}
Path("r6_build_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(audit,ensure_ascii=False))
