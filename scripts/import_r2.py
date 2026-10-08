#!/usr/bin/env python3
"""Acquire and audit 2020 (R2/46) historical exam from an archived real-question page.
No fabricated questions or answers. Fail closed if any choice / source key is missing.
This script runs in GitHub Actions with internet access; a successful fetch is frozen
as r2_meta.json and r2_source_excerpt.txt for subsequent reproducible builds.
"""
import hashlib
import html
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
SOURCE="https://ameblo.jp/gensan2155/entry-12768003510.html"
INDEPENDENT="https://gesuidou.link/gesan46/"
KEY=[
 2,2,2,3,3,3,1,1,3,3,3,2,2,1,3,1,4,2,3,1,
 4,2,2,1,2,4,4,3,4,2,1,4,2,1,3,1,4,4,1,3,
 4,1,3,4,3,1,2,4,4,3,2,4,1,4,1,2,3,3,2,1
]
assert len(KEY)==60

def n(s):
    return unicodedata.normalize("NFKC",html.unescape(s)).replace("\u00a0"," ").replace("\u3000"," ")

def fetch(url):
    rq=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; archival-study-audit/1.0)","Accept-Language":"ja,en;q=0.8"})
    with urlopen(rq,timeout=30) as r:
        data=r.read()
    if len(data)<10000: raise RuntimeError(f"Short source response {len(data)} bytes")
    return data

raw=fetch(SOURCE)
soup=BeautifulSoup(raw,"html.parser")
candidates=[]
for sel in [".skin-entryBody",".articleText",".article-text","[data-uranus-component='entryBody']","article",".entryBody","main","body"]:
    for node in soup.select(sel):
        txt=n(node.get_text("\n"))
        if len(re.findall(r"(?m)^\s*問\s*[0-9]{1,2}(?![0-9])",txt))>=50:
            candidates.append((len(txt),sel,node,txt))
if not candidates: raise RuntimeError("Could not find exam body with 50+ question markers")
_,selector,node,full=min(candidates,key=lambda a:a[0])
lines=[re.sub(r"[ \t]+"," ",n(x).strip()) for x in full.splitlines()]
lines=[line for line in lines if line]
text="\n".join(lines)
qmatches=list(re.finditer(r"(?m)^問\s*([0-9]{1,2})(?=\D|$)",text))
questions_in_order=[int(m.group(1)) for m in qmatches]
if questions_in_order!=list(range(1,61)):
    raise RuntimeError(f"Question sequence is not exactly 1..60: {questions_in_order}")
answer_section=re.search(r"(?m)^解答\s*$",text[qmatches[-1].end():])
if not answer_section:
    raise RuntimeError("Source answer section marker missing")
q60_end=qmatches[-1].end()+answer_section.start()
sections=[]
for i,m in enumerate(qmatches):
    end=qmatches[i+1].start() if i<59 else q60_end
    block=text[m.end():end].strip(" \n:-")
    choices=list(re.finditer(r"(?m)^\s*[\(（]([1-4])[\)）]\s*",block))
    nums=[int(c.group(1)) for c in choices]
    if nums!=[1,2,3,4]:
        raise RuntimeError(f"Q{i+1} choice markers {nums}, expected [1,2,3,4]")
    stem=re.sub(r"\s+"," ",block[:choices[0].start()]).strip()
    opts=[]
    for j,c in enumerate(choices):
        cend=choices[j+1].start() if j<3 else len(block)
        opts.append(re.sub(r"\s+"," ",block[c.end():cend]).strip())
    # Numeric choices like "6日" are legitimate and can be only two characters.
    if len(stem)<15 or any(len(o)<2 for o in opts):
        raise RuntimeError(f"Q{i+1} suspicious text: stem {len(stem)}, options {[len(x) for x in opts]}")
    sections.append((stem,opts))
a_start=qmatches[-1].end()+answer_section.end()
tail=text[a_start:]
rows=[]
for line in tail.splitlines():
    match=re.fullmatch(r"\s*([0-9]{1,2})\s+([1-4])\s+[0-9]{1,3}\s*",line)
    if match: rows.append((int(match.group(1)),int(match.group(2))))
if [q for q,a in rows]!=list(range(1,61)):
    raise RuntimeError(f"Source internal answer list not 1..60: {len(rows)} rows; tail sample {tail[:500]}")
found=[answer for _,answer in rows]
if found!=KEY:
    raise RuntimeError("Blog's internal answer key disagrees with the independent gesuidou.link/gesan46/ key, mismatch Qs "+str([i+1 for i,(a,b) in enumerate(zip(found,KEY)) if a!=b]))

# Categorization follows the 2020/46 official field distribution from a published exam-book sample.
def category(q):
    if q<=9: return "法令"
    if q<=25: return "水処理・汚泥"
    if q<=31: return "工場排水"
    if q<=54: return "運転管理"
    return "安全"

extracted=[]
for i,((stem,opts),answer) in enumerate(zip(sections,KEY),1):
    extracted.append({
       "id":f"R2-{i:02d}","year":"R2","yearLabel":"令和2年度・第46回","q":i,
       "category":category(i),"title":f"第46回 問{i}",
       "stem":stem,"choices":opts,"answer":answer,
       "explain":f"正答は（{answer}）。保存実問題の解答表と独立掲載の解答一覧が一致しています。詳細な理由解説は一次資料で未検証のため準備中です。",
       "trap":"設問文の「適切」「不適切」と条件をよく確認してください。",
       "memo":"解説は確認待ち。問題文と正答は照合済みです。","formula":""
    })
doc={
 "source":"令和2年度 第46回 実問題保存版。取得日2026-10-08。",
 "problemSource":SOURCE,"answerSource":INDEPENDENT,
 "source_sha256":hashlib.sha256(text.encode()).hexdigest(),
 "count":60,"questions":extracted
}
# Freeze compact original text and extraction only on full audit success.
(ROOT/"r2_source_excerpt.txt").write_text(text,encoding="utf-8")
(ROOT/"r2_meta.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
audit={
 "result":"PASS","selector":selector,"source_bytes":len(raw),
 "question_count":60,"choice_count":240,"internal_key_rows":60,"key_mismatches":0,
 "text_length":len(text),"source_sha256":doc["source_sha256"],
 "stem_lengths":[len(x[0]) for x in sections],
 "choice_min_length":min(len(o) for _,opts in sections for o in opts),
 "review_required":"Saved blog text is not the JSWA official PDF. Wording and tables should be visually inspected where the archive has anomalies."
}
(ROOT/"r2_import_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in audit.items() if k!="stem_lengths"},ensure_ascii=False))
