"""240-question integrity audit, deliberately separates structure from authenticity.

This checks local source manifests and answer references. It does not certify
that archived texts are verbatim JSWA examination papers or give reuse rights.
Do not change canonical source questions or answer keys here.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE_YEARS=("R7","R6","R3","R2")
HOLD_IDS=("R2-10","R2-15","R2-24","R2-30","R2-43","R2-48")
REPAIRED_IDS=("R2-17","R2-36")
EXAM_TOTAL=240

def read_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

questions={}
all_ids=set()
for year in SOURCE_YEARS:
    source=read_json(f"{year.lower()}_meta.json")
    items=source["questions"]
    assert len(items)==60,f"{year}: expected 60, found {len(items)}"
    ids=[]
    for q in items:
        n=q["q"]
        qid=f"{year}-{n:02d}"
        assert q["id"]==qid and q["year"]==year,(year,qid)
        assert isinstance(n,int) and 1<=n<=60
        assert q["answer"] in (1,2,3,4),qid
        assert isinstance(q.get("explain"),str) and q["explain"].strip(),qid
        assert isinstance(q.get("category"),str) and q["category"].strip(),qid
        if year in ("R2","R3"):
            assert isinstance(q.get("stem"),str) and len(q["stem"].strip())>=20,qid
            choices=q.get("choices")
            assert isinstance(choices,list) and len(choices)==4,qid
            assert all(isinstance(c,str) and c.strip() for c in choices),qid
            assert len(set(re.sub(r"\s+","",c) for c in choices))==4,qid
            assert all("\ufffd" not in c for c in choices),qid
        ids.append(qid)
    assert ids==[f"{year}-{n:02d}" for n in range(1,61)],year
    assert not all_ids.intersection(ids),year
    all_ids.update(ids)
    questions[year]=items
assert len(all_ids)==EXAM_TOTAL

review=read_json("research/explanation_review_v001.json")
reviewed={item["id"] for item in review["reviewed"]}
holds={item["id"] for item in review["holds"]}
assert holds==set(HOLD_IDS),f"Unexpected held questions: {sorted(holds)}"
assert len(reviewed)==23 and not reviewed.intersection(holds)
assert all(x in all_ids for x in holds|reviewed)
r3_review=read_json("research/r3_explanation_review_v001.json")
r3_reviewed={r["id"] for r in r3_review["reviewed"]}
assert r3_reviewed=={"R3-01","R3-03","R3-08","R3-09"}
assert all(x in all_ids for x in r3_reviewed)

# The existing two attempted repairs are transparent but should never be
# mistaken for a direct R2-official-original comparison.
source_repairs={q["id"] for q in questions["R2"] if q.get("sourceWarning")}
assert set(REPAIRED_IDS).issubset(source_repairs)
assert source_repairs==set(REPAIRED_IDS)|{"R2-43"}

# Known archival corruption and missing figures remain conservatively held.
q2={q["id"]:q for q in questions["R2"]}
assert "口内にあてはまる語" in q2["R2-30"]["choices"][3]
assert q2["R2-24"]["choices"][0].count("酸性減退期")==2
assert "図" in q2["R2-48"]["stem"] or "表" in q2["R2-48"]["stem"]
assert "A B C" in q2["R2-10"]["stem"]
assert q2["R2-15"]["answer"]==3 and "不適切" in q2["R2-15"]["stem"]

# Independent deterministic arithmetic consistency checks.
q3={q["id"]:q for q in questions["R3"]}
math_checks={
 "R2-11":(.43*5000/(1+.43),1500,3),
 "R2-17":((2000*1800)/(60*5000),12,4),
 "R2-36":((10000*(200-110)/1000)/30,30,1),
 "R3-23":(100*(1-.97)/(1-.85),20,2),
 "R3-37":(50/100*1000/(2500/1000),200,2),
 "R3-38":((10000*(200-110)/1000)/30,30,2),
}
for qid,(actual,expected,option) in math_checks.items():
    assert abs(actual-expected)<=max(1e-8,expected*.005),(qid,actual,expected)
    question=q2.get(qid) or q3[qid]
    assert question["answer"]==option,(qid,question["answer"],option)
    if question.get("choices"):
        val=question["choices"][option-1].replace(",","")
        assert str(expected) in val,(qid,val)
# The two repairs are *not* elevated to verified original-wording status by math.

report={
 "version":1,
 "audit_date":"2026-10-08",
 "scope":"Local source structure, answer-key consistency and deterministic arithmetic, not full page-by-page verbatim/source-rights review",
 "year_counts":{year:len(questions[year]) for year in SOURCE_YEARS},
 "total_archived_questions":EXAM_TOTAL,
 "excluded_from_grading":list(HOLD_IDS),
 "current_grading_pool":EXAM_TOTAL-len(holds),
 "r2_independently_reviewed_explanations":len(reviewed),
 "r3_independently_reviewed_explanations":len(r3_reviewed),
 "archival_repairs_without_direct_r2_official_comparison":list(REPAIRED_IDS),
 "r2_archival_table_warning":"R2-43",
 "arithmetic_checks":list(math_checks),
 "source_classes":{
   "R7":"Official PDF split into per-question images; cropped views checked separately by build_question_views.py",
   "R6":"Saved archive HTML split into 60 per-question views; validated separately",
   "R3":"Reconstructed or normalized saved question text; no direct JSWA original PDF comparison",
   "R2":"Saved blog text and answer list; original PDF direct comparison unresolved for some passages"
 },
 "finding":"STRUCTURE_PASS_WITH_SOURCE_LIMITATIONS",
 "critical_limits":[
   "60 correct answer numbers per year do not prove each original stem/choice matches the official paper.",
   "R2-17 and R2-36 have non-official archival text repairs; the arithmetic check cannot validate the historical original wording.",
   "R2 held six questions are excluded from graded study; still visible in reference-only mode.",
   "R3 and R2 archive wordings and all 240 published-question reuse conditions have not undergone a complete manual review.",
   "Only twenty-three R2 rationales and four R3 rationales have independent additional explanation review; the remaining explanations are not all audited."
 ]
}
out=ROOT/"research/question_integrity_audit_v001.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("QUESTION_INTEGRITY_PASS: 240 source rows, 6 holds, 2 repaired-wording warnings, 6 arithmetic checks, 23 reviewed R2 explanations, 4 R3 explanations")
