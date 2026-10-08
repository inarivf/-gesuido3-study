#!/usr/bin/env python3
"""Audit answer keys for years whose *real problem text* is still unavailable.

These keys MUST NOT be published as questions. Once a candidate original exam
is provided, validate its contents and metadata against these references before
any separate decision to release it to the quiz.
"""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REFERENCES=ROOT/"research"/"r4_r5_answer_keys_pending.json"

def validate_reference(doc):
    assert doc["status"]=="REFERENCE_KEYS_ONLY_NO_QUESTIONS", "Candidate answer key must never imply published questions"
    assert set(doc["years"])=={"R4","R5"}
    for label,year,round_number in (("R4",2022,48),("R5",2023,49)):
        item=doc["years"][label]
        assert item["year"]==year and item["round"]==round_number
        assert item["status"]=="SOURCE_PENDING"
        assert item["expected_questions"]==60
        assert len(item["answers"])==60
        assert len(item.get("sources",[]))>=2
        for number,answer in enumerate(item["answers"],1):
            if label=="R5" and number==16:
                assert answer is None, "R5 Q16 must not have a correct option"
            else:
                assert type(answer) is int and 1<=answer<=4, f"{label} Q{number} invalid answer"
        if label=="R5":
            exclusions=item["restrictions"]
            assert len(exclusions)==1
            x=exclusions[0]
            assert x["question"]==16 and x["status"]=="VOID" and x["score_value"]==1
            assert x["official_handling"]=="全員に1点付与"
            assert item["grading"]=={"method":"all-questions-60-points","bonus":1,"exception_question":16}
        else:
            assert item["restrictions"]==[]
            assert item["grading"]=={"method":"normal","bonus":0}
    return True

def evaluate_score(year,choices,references):
    """Faithful historical scoring, NOT intended to create an R5 quiz."""
    ref=references["years"][year]
    if len(choices)!=60:
        raise ValueError("Expected 60 marked positions")
    score=0
    for q,(correct,choice) in enumerate(zip(ref["answers"],choices),1):
        if year=="R5" and q==16:
            score+=1  # full credit regardless of choice, including blank
        elif choice in (1,2,3,4) and choice==correct:
            score+=1
    return score

def validate_candidate(candidate,refs):
    """Reject non-original/incomplete questions; do not auto-publish on PASS."""
    label=candidate.get("year")
    assert label in ("R4","R5"), "Only R4 or R5 accepted"
    src=candidate.get("sourceEvidence",{})
    assert src.get("type") in ("official_pdf","owner_supplied_exam_scan","verifiable_exam_archive"), "Original source evidence required"
    assert src.get("uri"), "Missing original archive/document reference"
    assert len(src.get("sha256",""))==64, "Missing SHA-256 of source bytes"
    assert candidate.get("releaseApproved") is not True, "Candidate input may not self-approve publication"
    qs=candidate.get("questions",[])
    assert len(qs)==60, "Must have all 60 questions"
    by_n={}
    for q in qs:
        n=q.get("q")
        assert type(n) is int and 1<=n<=60 and n not in by_n, "Question number missing/duplicate"
        by_n[n]=q
        assert len(str(q.get("stem","")).strip())>=15, f"Q{n} has no useful question text"
        choices=q.get("choices")
        assert isinstance(choices,list) and len(choices)==4 and all(isinstance(x,str) and len(x.strip())>=1 for x in choices), f"Q{n} choices missing"
        if label=="R5" and n==16:
            assert q.get("answer") is None and q.get("status")=="VOID" and q.get("score_value")==1, "R5 Q16 needs all-person-credit"
        else:
            assert q.get("answer")==refs["years"][label]["answers"][n-1], f"Q{n} answer mismatch"
    assert sorted(by_n)==list(range(1,61))
    # This is a mechanical pre-audit only. Figures and source fidelity still
    # require comparison against original PDF before manual release approval.
    return {"result":"CANDIDATE_STRUCTURAL_PASS_NOT_RELEASE_APPROVAL","year":label,"questions":60,
            "scored_positions":60,"requires_manual_source_and_figure_review":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",type=Path)
    args=p.parse_args()
    refs=json.loads(REFERENCES.read_text(encoding="utf-8"))
    validate_reference(refs)
    for label in ("R4","R5"):
        full=[*refs["years"][label]["answers"]]
        blank=[None]*60
        if label=="R5": full[15]=None
        assert evaluate_score(label,full,refs)==60
        assert evaluate_score(label,blank,refs)==(1 if label=="R5" else 0)
    if args.candidate:
        result=validate_candidate(json.loads(args.candidate.read_text(encoding="utf-8")),refs)
    else:
        result={"result":"PENDING_KEYS_AUDIT_PASS","r4_key_count":60,"r5_key_count":60,
                "r5_q16":"VOID_ALL_CANDIDATES_1_POINT","published_questions_added":0}
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
    main()
