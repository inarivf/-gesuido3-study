import json, os, re, subprocess, unicodedata
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/"r7_mondai_3syu_official.pdf"
R7_PAGES=ROOT/"r7_pages"
R7_OUT=ROOT/"r7_questions"
R6_ARCHIVE=ROOT/"r6_archive.html"
R6_OUT=ROOT/"r6_questions"

R7_OUT.mkdir(exist_ok=True)
R6_OUT.mkdir(exist_ok=True)

# ---------- R7: official PDF -> exact one-question image crops ----------
bbox=ROOT/".r7_bbox.html"
subprocess.run(["pdftotext","-bbox-layout",str(PDF),str(bbox)],check=True)
soup=BeautifulSoup(bbox.read_text(encoding="utf-8",errors="ignore"),"html.parser")
pages=soup.find_all("page")
if len(pages)!=29:
    raise RuntimeError(f"R7 PDF expected 29 pages, got {len(pages)}")

starts={}
page_meta={}
for page_no,page in enumerate(pages,1):
    pw=float(page.get("width"))
    ph=float(page.get("height"))
    page_meta[page_no]={"width":pw,"height":ph}
    for line in page.find_all("line"):
        words=line.find_all("word")
        if not words:
            continue
        txt="".join(w.get_text("",strip=True) for w in words)
        norm=unicodedata.normalize("NFKC",txt)
        norm=re.sub(r"\s+","",norm)
        m=re.match(r"^問([0-9]{1,2})(?:\D|$)",norm)
        if not m:
            continue
        q=int(m.group(1))
        if not (1<=q<=60):
            continue
        x=min(float(w.get("xmin")) for w in words)
        y=min(float(w.get("ymin")) for w in words)
        # Question headers are near the left margin. Ignore accidental body mentions.
        if x>180:
            continue
        prev=starts.get(q)
        if prev is None or (page_no,y)<(prev["page"],prev["y"]):
            starts[q]={"page":page_no,"x":x,"y":y}

missing=[q for q in range(1,61) if q not in starts]
if missing:
    raise RuntimeError(f"R7 bbox detection missing questions: {missing}")
if len(starts)!=60:
    raise RuntimeError(f"R7 bbox detection expected 60, got {len(starts)}")

# Sanity: question order must never go backwards by PDF position.
ordered=[(q,starts[q]["page"],starts[q]["y"]) for q in range(1,61)]
for (qa,pa,ya),(qb,pb,yb) in zip(ordered,ordered[1:]):
    if (pb,yb)<(pa,ya):
        raise RuntimeError(f"R7 order error Q{qa} -> Q{qb}")

# Remove old generated crops first.
for p in R7_OUT.glob("q-*.jpg"):
    p.unlink()

crop_map={}
for q in range(1,61):
    info=starts[q]
    page_no=info["page"]
    pw=page_meta[page_no]["width"]
    ph=page_meta[page_no]["height"]
    same=[(n,starts[n]["y"]) for n in range(q+1,61) if starts[n]["page"]==page_no]
    next_y=min((y for _,y in same),default=None)

    top_pt=max(0.0,info["y"]-9.0)
    bottom_pt=(next_y-7.0) if next_y is not None else (ph-24.0)
    if bottom_pt-top_pt<70:
        raise RuntimeError(f"R7 crop too short Q{q}: {bottom_pt-top_pt:.1f}pt")

    page_img=R7_PAGES/f"page-{page_no:03d}.jpg"
    if not page_img.exists():
        raise RuntimeError(f"Missing R7 rendered page {page_img.name}")
    with Image.open(page_img) as im:
        sx=im.width/pw
        sy=im.height/ph
        left=int(max(0,22*sx))
        right=int(min(im.width,(pw-22)*sx))
        top=int(max(0,top_pt*sy))
        bottom=int(min(im.height,bottom_pt*sy))
        crop=im.crop((left,top,right,bottom)).convert("RGB")
        # Small white padding improves mobile readability.
        pad=12
        out=Image.new("RGB",(crop.width+pad*2,crop.height+pad*2),"white")
        out.paste(crop,(pad,pad))
        dest=R7_OUT/f"q-{q:03d}.jpg"
        out.save(dest,"JPEG",quality=88,optimize=True,progressive=True)

    crop_map[str(q)]={
        "page":page_no,
        "top_pt":round(top_pt,2),
        "bottom_pt":round(bottom_pt,2),
        "file":f"r7_questions/q-{q:03d}.jpg"
    }

(ROOT/"r7_question_map.json").write_text(
    json.dumps({
        "source":"JSWA R7 official PDF",
        "method":"pdftotext -bbox-layout + exact header detection + crop",
        "questions":crop_map
    },ensure_ascii=False,indent=2),
    encoding="utf-8"
)

# ---------- R6: archived real exam -> one-question HTML files ----------
raw=R6_ARCHIVE.read_text(encoding="utf-8")
s6=BeautifulSoup(raw,"html.parser")
anchors=[]
for q in range(1,61):
    a=s6.find(id=f"r6q{q}")
    if a is None:
        raise RuntimeError(f"R6 missing anchor r6q{q}")
    anchors.append(a)

for p in R6_OUT.glob("q-*.html"):
    p.unlink()

css="""
:root{color-scheme:light}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,sans-serif;color:#17242a;background:#fff;margin:0;padding:12px;line-height:1.7}
main{max-width:900px;margin:auto}
.question-start{background:#eaf7f9;border-left:5px solid #087c91;padding:8px 10px;border-radius:8px;margin-top:0}
p,li{font-size:.98rem}
img{max-width:100%;height:auto}
table{width:100%;border-collapse:collapse;margin:8px 0;font-size:.9rem}td,th{border:1px solid #ccd8dc;padding:6px;vertical-align:top}
.source{font-size:.78rem;color:#657981;border-top:1px solid #e0e8ea;margin-top:12px;padding-top:8px}
"""

for q,a in enumerate(anchors,1):
    parts=[str(a)]
    sib=a.next_sibling
    while sib is not None:
        if isinstance(sib,Tag):
            if "question-start" in (sib.get("class") or []):
                break
            # Stop at section headings such as 問21〜40.
            if sib.name in ("h1","h2","h3") and re.search(r"問\s*\d+",sib.get_text(" ",strip=True)):
                break
            parts.append(str(sib))
        else:
            parts.append(str(sib))
        sib=sib.next_sibling

    body=BeautifulSoup("".join(parts),"html.parser")
    for img in body.find_all("img"):
        src=img.get("src","")
        if src.startswith("r6_assets/"):
            img["src"]="../"+src

    title=a.get_text(" ",strip=True)
    doc=f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title><style>{css}</style></head><body><main>{body}<div class='source'>令和6年度 第50回 下水道技術検定 第3種 実問題。保存アーカイブより収録。</div></main></body></html>"""
    (R6_OUT/f"q-{q:03d}.html").write_text(doc,encoding="utf-8")

audit={
    "version":"1.1",
    "r7_detected_questions":len(starts),
    "r7_crops":len(list(R7_OUT.glob("q-*.jpg"))),
    "r6_question_pages":len(list(R6_OUT.glob("q-*.html"))),
    "r7_page_distribution":{str(p):sum(1 for q in starts if starts[q]["page"]==p) for p in sorted({starts[q]["page"] for q in starts})},
    "r7_last_questions":{str(q):starts[q] for q in range(55,61)}
}
(ROOT/"question_view_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
bbox.unlink(missing_ok=True)
print(json.dumps(audit,ensure_ascii=False))
