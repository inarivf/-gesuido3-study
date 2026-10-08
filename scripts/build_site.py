import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
tpl=(ROOT/"site_template.html").read_text(encoding="utf-8")
r7=json.loads((ROOT/"r7_meta.json").read_text(encoding="utf-8"))
r6=json.loads((ROOT/"r6_meta.json").read_text(encoding="utf-8"))
r3=json.loads((ROOT/"r3_meta.json").read_text(encoding="utf-8"))

for name,data in [("R7",r7),("R6",r6),("R3",r3)]:
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
        if name=="R3":
            if not q.get("stem"):
                raise RuntimeError(f"R3: missing stem in {q.get('id')}")
            if not isinstance(q.get("choices"),list) or len(q["choices"])!=4 or any(not str(x).strip() for x in q["choices"]):
                raise RuntimeError(f"R3: invalid choices in {q.get('id')}")

r7_json=json.dumps(r7["questions"],ensure_ascii=False,separators=(",",":"))
r6_json=json.dumps(r6["questions"],ensure_ascii=False,separators=(",",":"))
r3_json=json.dumps(r3["questions"],ensure_ascii=False,separators=(",",":"))
html=tpl.replace("__R7__",r7_json).replace("__R6__",r6_json).replace("__R3__",r3_json)
if "__R7__" in html or "__R6__" in html or "__R3__" in html:
    raise RuntimeError("template placeholders remain")

(ROOT/"index.html").write_text(html,encoding="utf-8")
manifest={
    "version":"1.2",
    "generated_from":["site_template.html","r7_meta.json","r6_meta.json","r3_meta.json","r7_question_map.json","r6_questions/"],
    "question_counts":{"R7":60,"R6":60,"R3":60,"total":180},
    "r7_source":"日本下水道事業団 令和7年度 第51回 第3種 公式問題PDF（1問単位ビュー生成）",
    "r6_source":"保存実問題アーカイブ（1問単位ビュー生成）。正答60問照合済み",
    "r3_source":"令和3年度 第47回 実問題保存本文を整形表示。独立正答資料と60問照合済み",
    "generated_file":"index.html"
}
(ROOT/"site_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False))
