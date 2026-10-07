import json,re,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
errors=[]

def fail(msg): errors.append(msg)

for file in ["index.html","site_template.html","r7_meta.json","r6_meta.json","r6_build_audit.json","r7_mondai_3syu_official.pdf","r6_archive.html","r7_question_map.json","question_view_audit.json"]:
    if not (ROOT/file).exists():
        fail(f"missing {file}")

if not errors:
    r7=json.loads((ROOT/"r7_meta.json").read_text(encoding="utf-8"))["questions"]
    r6=json.loads((ROOT/"r6_meta.json").read_text(encoding="utf-8"))["questions"]
    allq=r7+r6
    if len(r7)!=60: fail(f"R7 count {len(r7)}")
    if len(r6)!=60: fail(f"R6 count {len(r6)}")
    if len(allq)!=120: fail(f"total count {len(allq)}")
    ids=[q["id"] for q in allq]
    if len(ids)!=len(set(ids)): fail("duplicate question IDs")
    bad=[q["id"] for q in allq if q.get("answer") not in [1,2,3,4]]
    if bad: fail("invalid answers: "+",".join(bad))

    qmap=json.loads((ROOT/"r7_question_map.json").read_text(encoding="utf-8")).get("questions",{})
    if len(qmap)!=60: fail(f"R7 question crop map count {len(qmap)}")
    for n in range(1,61):
        if str(n) not in qmap: fail(f"R7 missing question crop Q{n}")
        if not (ROOT/f"r7_questions/q-{n:03d}.jpg").exists(): fail(f"R7 missing crop q-{n:03d}.jpg")
        if not (ROOT/f"r6_questions/q-{n:03d}.html").exists(): fail(f"R6 missing question page q-{n:03d}.html")
    qview=json.loads((ROOT/"question_view_audit.json").read_text(encoding="utf-8"))
    if qview.get("r7_detected_questions")!=60: fail(f"R7 bbox detected {qview.get('r7_detected_questions')}")
    if qview.get("r7_crops")!=60: fail(f"R7 crop count {qview.get('r7_crops')}")
    if qview.get("r6_question_pages")!=60: fail(f"R6 question page count {qview.get('r6_question_pages')}")

    audit=json.loads((ROOT/"r6_build_audit.json").read_text(encoding="utf-8"))
    if audit.get("questions")!=60: fail(f"R6 archive questions {audit.get('questions')}")
    if audit.get("answers_found")!=60: fail(f"R6 answers found {audit.get('answers_found')}")
    if audit.get("answer_mismatch"): fail(f"R6 answer mismatch {audit.get('answer_mismatch')}")
    if audit.get("anchor_warning"): fail(f"R6 anchor warning {audit.get('anchor_warning')}")
    if audit.get("answer_warning"): fail(f"R6 answer warning {audit.get('answer_warning')}")

    html=(ROOT/"index.html").read_text(encoding="utf-8")
    required=[
        "v1.1","実過去問120問","R7_QUESTIONS","R6_QUESTIONS",
        "startMode('random20')","startMode('weak')","startMode('mock')",
        "./r7_questions/q-","./r6_questions/q-","gesuido3_progress_v1"
    ]
    for x in required:
        if x not in html: fail(f"index missing marker: {x}")
    forbidden=["docs.google.com/gview","id=\"officialPdf\"","v0.6","v0.7","v0.8","./r7_pages/page-"]
    for x in forbidden:
        if x in html: fail(f"index contains obsolete marker: {x}")
    if html.count("__R7__") or html.count("__R6__"): fail("unreplaced placeholders")
    if len(re.findall(r'"id":"R7-',html))!=60: fail("embedded R7 count not 60")
    if len(re.findall(r'"id":"R6-',html))!=60: fail("embedded R6 count not 60")

    archive=(ROOT/"r6_archive.html").read_text(encoding="utf-8")
    for n in range(1,61):
        if f'id="r6q{n}"' not in archive and f"id='r6q{n}'" not in archive:
            fail(f"R6 archive missing anchor r6q{n}")

if errors:
    print("VALIDATION FAILED")
    for e in errors: print(" -",e)
    sys.exit(1)
print("VALIDATION PASS: v1.1, 120 questions, one-question views 60/60 + 60/60, no answer mismatch")
