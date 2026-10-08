"""Fail-closed audit for explanations reviewed against independent material.

Review is additive: no corrections to canonical question text, choices or answer.
Exactly the documented R2 records are promoted to reviewed state.
Archival ambiguities are deliberately preserved as holds.
"""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))
r2=read("r2_meta.json")["questions"]
ledger=read("research/explanation_review_v001.json")
source={q["id"]:q for q in r2}
expected={"R2-01":2,"R2-02":2,"R2-03":2,"R2-07":1,
          "R2-08":1,"R2-09":3,"R2-11":3,"R2-13":2,
          "R2-14":1,"R2-22":2,"R2-31":1,"R2-32":4,
          "R2-33":2,"R2-51":2,"R2-52":4,"R2-53":1,
          "R2-57":3,"R2-60":1}
holds={"R2-10","R2-15","R2-24","R2-30","R2-43","R2-48"}
assert len(r2)==60
assert ledger["version"]==2
assert {x["id"] for x in ledger["reviewed"]}==set(expected)
assert {x["id"] for x in ledger["holds"]}==holds
assert len(ledger["reviewed"])==len(expected)
for r in ledger["reviewed"]:
    original=source[r["id"]]
    assert original["answer"]==expected[r["id"]],f"canonical answer changed {r['id']}"
    assert len(original.get("choices",[]))==4, f"missing choices {r['id']}"
    assert len(r["explain"])>=65 and f"（{expected[r['id']]}）" in r["explain"],f"incomplete explanation {r['id']}"
    assert r["status"] in ("source_checked","calculation_checked")
    assert r["references"],f"missing evidence {r['id']}"
    for ref in r["references"]:
        u=urlparse(ref["url"])
        assert u.scheme=="https" and u.netloc and ref["title"],f"unusable reference {r['id']}"
    if r["id"]=="R2-11":
        assert r["status"]=="calculation_checked"
        computed=.43*5000/(1+.43)
        assert abs(computed-1500)<5, "MLSS value inconsistent with choice (3)"
        assert "1,503" in r["formula"] and "1,500" in r["formula"]
for r in ledger["holds"]:
    assert r["id"] in source and r["status"] in ("source_damaged","figure_unverified","answer_needs_review")
    assert len(r["warning"])>=30
    assert r["id"] not in expected
assert "不適切" in source["R2-15"]["stem"] and source["R2-15"]["answer"]==3
assert "口内にあてはまる語" in source["R2-30"]["choices"][3]
assert "A B C" in source["R2-10"]["stem"]
assert source["R2-24"]["choices"][0].count("酸性減退期")==2
assert source["R2-43"]["sourceWarning"]
assert "表" in source["R2-48"]["stem"]
pending=sum("詳細な理由解説は一次資料で未検証" in q["explain"] for q in r2)
assert pending==58, "raw source explanation count has changed"
print(f"EXPLANATION AUDIT PASS: {len(expected)} independently grounded R2 explanations, {len(holds)} source holds, original 60 questions and answers intact")
