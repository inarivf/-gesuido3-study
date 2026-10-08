import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_pending_years import REFERENCES,validate_reference,evaluate_score,validate_candidate

class PendingYearAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.refs=json.loads(REFERENCES.read_text(encoding="utf-8"))
    def test_references(self):
        self.assertTrue(validate_reference(self.refs))
    def test_normal_score(self):
        expected=self.refs["years"]["R4"]["answers"]
        self.assertEqual(evaluate_score("R4",expected,self.refs),60)
        self.assertEqual(evaluate_score("R4",[None]*60,self.refs),0)
    def test_void_problem_full_credit(self):
        self.assertEqual(evaluate_score("R5",[None]*60,self.refs),1)
        expected=self.refs["years"]["R5"]["answers"]
        self.assertEqual(evaluate_score("R5",expected,self.refs),60)
        guessed=expected[:]
        guessed[15]=1
        self.assertEqual(evaluate_score("R5",guessed,self.refs),60)
        guessed[15]=4
        self.assertEqual(evaluate_score("R5",guessed,self.refs),60)
    def test_candidate_cannot_fake_full_exam(self):
        broken={"year":"R5","sourceEvidence":{"type":"verifiable_exam_archive","uri":"example","sha256":"a"*64},"questions":[]}
        with self.assertRaises(AssertionError):
            validate_candidate(broken,self.refs)
    def test_candidate_q16_cannot_be_standard_question(self):
        qset=[]
        for i,n in enumerate(self.refs["years"]["R5"]["answers"],1):
            qset.append({"q":i,"stem":"保存原本から取得したというテスト用の仮データ・公開不可。","choices":["選択肢1","選択肢2","選択肢3","選択肢4"],"answer":n})
        source={"type":"verifiable_exam_archive","uri":"example.test/archived","sha256":"f"*64}
        c={"year":"R5","sourceEvidence":source,"questions":qset}
        with self.assertRaises(AssertionError): validate_candidate(c,self.refs)
        qset[15].update({"status":"VOID","score_value":1})
        result=validate_candidate(c,self.refs)
        self.assertEqual(result["result"],"CANDIDATE_STRUCTURAL_PASS_NOT_RELEASE_APPROVAL")
        c["releaseApproved"]=True
        with self.assertRaises(AssertionError):validate_candidate(c,self.refs)

if __name__=="__main__":
    unittest.main(verbosity=2)
