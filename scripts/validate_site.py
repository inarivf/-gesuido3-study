import json,re,sys,unicodedata
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
errors=[]

R7_OFFICIAL_KEY=[
    4,4,3,1,2,1,3,2,4,2,1,3,3,2,1,2,4,1,2,3,
    3,1,4,2,2,1,3,4,1,1,4,3,3,1,2,2,4,4,2,3,
    2,4,1,1,3,4,1,2,4,3,4,4,4,1,3,2,2,1,3,3
]
R6_EXECUTOR_KEY=[
    2,4,3,1,2,3,4,1,1,2,1,3,2,1,2,4,1,3,2,4,
    4,4,1,3,3,3,1,2,1,3,4,4,1,1,2,4,2,3,4,2,
    3,1,2,1,4,3,3,4,2,4,3,2,4,2,4,1,3,2,3,1
]
R3_ARCHIVE_KEY=[
    3,4,1,3,4,2,3,4,4,1,3,1,4,3,4,1,4,2,1,2,
    1,3,2,2,4,3,1,3,1,1,3,2,3,2,4,4,2,2,3,2,
    2,4,3,3,1,2,2,4,4,4,1,3,1,2,3,1,1,2,4,4
]
R2_ARCHIVE_KEY=[
    2,2,2,3,3,3,1,1,3,3,3,2,2,1,3,1,4,2,3,1,
    4,2,2,1,2,4,4,3,4,2,1,4,2,1,3,1,4,4,1,3,
    4,1,3,4,3,1,2,4,4,3,2,4,1,4,1,2,3,3,2,1
]

def fail(msg): errors.append(msg)

def norm_text(value):
    return unicodedata.normalize("NFKC",value or "").replace("\u3000"," ")

for file in ["index.html","site_template.html","r7_meta.json","r6_meta.json","r3_meta.json","r2_meta.json","r2_import_audit.json","r2_source_excerpt.txt","r6_build_audit.json","r7_mondai_3syu_official.pdf","r6_archive.html","r7_question_map.json","question_view_audit.json"]:
    if not (ROOT/file).exists():
        fail(f"missing {file}")

if not errors:
    r7=json.loads((ROOT/"r7_meta.json").read_text(encoding="utf-8"))["questions"]
    r6=json.loads((ROOT/"r6_meta.json").read_text(encoding="utf-8"))["questions"]
    r3=json.loads((ROOT/"r3_meta.json").read_text(encoding="utf-8"))["questions"]
    r2=json.loads((ROOT/"r2_meta.json").read_text(encoding="utf-8"))["questions"]
    allq=r7+r6+r3+r2
    if len(r7)!=60: fail(f"R7 count {len(r7)}")
    if len(r6)!=60: fail(f"R6 count {len(r6)}")
    if len(r3)!=60: fail(f"R3 count {len(r3)}")
    if len(r2)!=60: fail(f"R2 count {len(r2)}")
    if len(allq)!=240: fail(f"total count {len(allq)}")
    ids=[q["id"] for q in allq]
    if len(ids)!=len(set(ids)): fail("duplicate question IDs")
    bad=[q["id"] for q in allq if q.get("answer") not in [1,2,3,4]]
    if bad: fail("invalid answers: "+",".join(bad))

    # Canonical identity + answer-key audit.
    for label,qs,key,round_label in [
        ("R7",r7,R7_OFFICIAL_KEY,"令和7年度・第51回"),
        ("R6",r6,R6_EXECUTOR_KEY,"令和6年度・第50回"),
        ("R3",r3,R3_ARCHIVE_KEY,"令和3年度・第47回"),
        ("R2",r2,R2_ARCHIVE_KEY,"令和2年度・第46回"),
    ]:
        by_q={int(q.get("q",0)):q for q in qs}
        if sorted(by_q)!=list(range(1,61)):
            fail(f"{label} question numbers are not exactly 1..60")
        for n in range(1,61):
            q=by_q.get(n)
            if q is None:
                continue
            expected_id=f"{label}-{n:02d}"
            if q.get("id")!=expected_id:
                fail(f"{label} Q{n} id {q.get('id')} != {expected_id}")
            if q.get("year")!=label:
                fail(f"{label} Q{n} year {q.get('year')} != {label}")
            if q.get("yearLabel")!=round_label:
                fail(f"{label} Q{n} yearLabel {q.get('yearLabel')} != {round_label}")
            if int(q.get("answer",0))!=key[n-1]:
                fail(f"{label} Q{n} answer {q.get('answer')} != canonical {key[n-1]}")
            if label in ("R3","R2"):
                if not str(q.get("stem","")).strip():
                    fail(f"R3 Q{n} missing stem")
                choices=q.get("choices")
                if not isinstance(choices,list) or len(choices)!=4 or any(not str(c).strip() for c in choices):
                    fail(f"R3 Q{n} choices invalid")

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
    if qview.get("r7_choice_marker_checks")!=60: fail(f"R7 choice marker checks {qview.get('r7_choice_marker_checks')}")
    if qview.get("r7_choice_marker_failures"): fail(f"R7 choice marker failures {qview.get('r7_choice_marker_failures')}")

    audit=json.loads((ROOT/"r6_build_audit.json").read_text(encoding="utf-8"))
    if audit.get("questions")!=60: fail(f"R6 archive questions {audit.get('questions')}")
    if audit.get("answers_found")!=60: fail(f"R6 answers found {audit.get('answers_found')}")
    if audit.get("answer_mismatch"): fail(f"R6 answer mismatch {audit.get('answer_mismatch')}")
    if audit.get("anchor_warning"): fail(f"R6 anchor warning {audit.get('anchor_warning')}")
    if audit.get("answer_warning"): fail(f"R6 answer warning {audit.get('answer_warning')}")

    r2audit=json.loads((ROOT/"r2_import_audit.json").read_text(encoding="utf-8"))
    if r2audit.get("result")!="PASS": fail("R2 import audit not PASS")
    if r2audit.get("question_count")!=60: fail("R2 source count not 60")
    if r2audit.get("choice_count")!=240: fail("R2 source choices not 240")
    if r2audit.get("internal_key_rows")!=30: fail("R2 first-30 blog key incomplete")
    if r2audit.get("independent_key_rows")!=60: fail("R2 independent key not 60")
    if r2audit.get("key_mismatches")!=0: fail("R2 source answer mismatch")
    if r2audit.get("documented_source_repairs")!=[17,36]: fail("R2 source repairs missing")
    if r2audit.get("source_warning_qs")!=[17,36,43]: fail("R2 source warnings missing")
    if "余剰汚泥量: 60m3/日" not in r2[16].get("stem",""):
        fail("R2 Q17 retained inconsistent old 160m3/日")
    if "5,000mg/L" not in r2[16].get("stem",""):
        fail("R2 Q17 SS unit not repaired")
    if "流出水SS濃度: 110mg/L" not in r2[35].get("stem",""):
        fail("R2 Q36 SS unit not repaired")
    if r2[35].get("choices",[])[2]!="50m3/日":
        fail("R2 Q36 choice 3 not repaired")
    for n in (17,36,43):
        if not r2[n-1].get("sourceWarning"):
            fail(f"R2 Q{n} missing original-source warning")
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    required=[
        "v1.4","実過去問240問","R7_QUESTIONS","R6_QUESTIONS","R3_QUESTIONS","R2_QUESTIONS",
        "startMode('random20')","startMode('weak')","startMode('mock')",
        "./r7_questions/q-","./r6_questions/q-","gesuido3_progress_v1"
    ]
    for x in required:
        if x not in html: fail(f"index missing marker: {x}")
    forbidden=["docs.google.com/gview","id=\"officialPdf\"","v0.6","v0.7","v0.8","./r7_pages/page-"]
    for x in forbidden:
        if x in html: fail(f"index contains obsolete marker: {x}")
    if html.count("__R7__") or html.count("__R6__") or html.count("__R3__") or html.count("__R2__"): fail("unreplaced placeholders")
    if len(re.findall(r'"id":"R7-',html))!=60: fail("embedded R7 count not 60")
    if len(re.findall(r'"id":"R6-',html))!=60: fail("embedded R6 count not 60")
    if len(re.findall(r'"id":"R3-',html))!=60: fail("embedded R3 count not 60")
    if len(re.findall(r'"id":"R2-',html))!=60: fail("embedded R2 count not 60")

    archive=(ROOT/"r6_archive.html").read_text(encoding="utf-8")
    archive_soup=BeautifulSoup(archive,"html.parser")
    for n in range(1,61):
        if f'id="r6q{n}"' not in archive and f"id='r6q{n}'" not in archive:
            fail(f"R6 archive missing anchor r6q{n}")

        # The generated one-question view must still contain the correct question header
        # and all four answer choices. Q6 uses a table, so support both (1)-(4) markers
        # and exact table-cell numerals 1..4.
        qfile=ROOT/f"r6_questions/q-{n:03d}.html"
        if qfile.exists():
            qsoup=BeautifulSoup(qfile.read_text(encoding="utf-8"),"html.parser")
            plain=norm_text(qsoup.get_text(" ",strip=True))
            if re.search(rf"問\s*0*{n}(?:\D|$)",plain) is None:
                fail(f"R6 generated view Q{n} missing its question header")
            paren_ok=all(f"({k})" in plain for k in range(1,5))
            cell_values={norm_text(td.get_text(" ",strip=True)).strip() for td in qsoup.find_all("td")}
            table_ok=all(str(k) in cell_values for k in range(1,5))
            if not (paren_ok or table_ok):
                fail(f"R6 generated view Q{n} missing one or more answer choices")

if errors:
    print("VALIDATION FAILED")
    for e in errors: print(" -",e)
    sys.exit(1)
print("VALIDATION PASS: v1.4, 240 questions, identity/answer keys checked, R3/R2 stems/choices checked, one-question views R7 60/60 + R6 60/60")
