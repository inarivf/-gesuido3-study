import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
tpl=(ROOT/"site_template.html").read_text(encoding="utf-8")
r7=json.loads((ROOT/"r7_meta.json").read_text(encoding="utf-8"))
r6=json.loads((ROOT/"r6_meta.json").read_text(encoding="utf-8"))
r3=json.loads((ROOT/"r3_meta.json").read_text(encoding="utf-8"))
r2=json.loads((ROOT/"r2_meta.json").read_text(encoding="utf-8"))
reviews=json.loads((ROOT/"research/explanation_review_v001.json").read_text(encoding="utf-8"))
r2_by_id={q["id"]:q for q in r2["questions"]}
for record in reviews["reviewed"]:
    q=r2_by_id[record["id"]]
    # Preserve original question text, all choices and the canonical answer.
    q["explain"]=record["explain"]
    if "formula" in record:q["formula"]=record["formula"]
    q["reviewStatus"]=record["status"]
    q["reviewReferences"]=record["references"]
for record in reviews["holds"]:
    q=r2_by_id[record["id"]]
    q["explanationWarning"]=record["warning"]
    q["reviewStatus"]=record["status"]

for name,data in [("R7",r7),("R6",r6),("R3",r3),("R2",r2)]:
    qs=data.get("questions",[])
    if len(qs)!=60:
        raise RuntimeError(f"{name}: expected 60 questions, got {len(qs)}")
    ids=[q["id"] for q in qs]
    if len(ids)!=len(set(ids)):
        raise RuntimeError(f"{name}: duplicate IDs")
    for q in qs:
        if int(q.get("answer",0)) not in (1,2,3,4):
            raise RuntimeError(f"{name}: invalid answer {q.get('id')}")
        for key in ("id","year","q","category","title","explain"):
            if key not in q:
                raise RuntimeError(f"{name}: missing {key} in {q.get('id')}")
        if name in ("R3","R2"):
            if not q.get("stem"):
                raise RuntimeError(f"R3: missing stem in {q.get('id')}")
            if not isinstance(q.get("choices"),list) or len(q["choices"])!=4 or any(not str(x).strip() for x in q["choices"]):
                raise RuntimeError(f"R3: invalid choices in {q.get('id')}")

r7_json=json.dumps(r7["questions"],ensure_ascii=False,separators=(",",":"))
r6_json=json.dumps(r6["questions"],ensure_ascii=False,separators=(",",":"))
r3_json=json.dumps(r3["questions"],ensure_ascii=False,separators=(",",":"))
r2_json=json.dumps(r2["questions"],ensure_ascii=False,separators=(",",":"))
html=tpl.replace("__R7__",r7_json).replace("__R6__",r6_json).replace("__R3__",r3_json).replace("__R2__",r2_json)
if "__R7__" in html or "__R6__" in html or "__R3__" in html or "__R2__" in html:
    raise RuntimeError("template placeholders remain")

(ROOT/"index.html").write_text(html,encoding="utf-8")
manifest={
    "version":"1.14",
    "generated_from":["site_template.html","r7_meta.json","r6_meta.json","r3_meta.json","r2_meta.json","research/explanation_review_v001.json","r7_question_map.json","r6_questions/"],
    "question_counts":{"R7":60,"R6":60,"R3":60,"R2":60,"total":240},
    "r7_source":"日本下水道事業団 令和7年度 第51回 第3種 公式問題PDF（1問単位ビュー生成）",
    "r6_source":"保存実問題アーカイブ（1問単位ビュー生成）。正答60問照合済み",
    "r3_source":"令和3年度 第47回 実問題保存本文を整形表示。独立正答資料と60問照合済み",
    "r2_source":"令和2年度 第46回 実問題保存本文。独立正答資料と60問照合済み。解説は個別に独立監査中",
    "generated_file":"index.html"
}
(ROOT/"site_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False))
