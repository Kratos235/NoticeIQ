"""
test_noticeiq.py
================
Simple unit tests for the NoticeIQ AI logic (analyzer + scoring).
Run with:
    python -m unittest test_noticeiq.py
These tests do NOT require a database (they test pure functions only).
"""
import unittest
from datetime import date, timedelta

import analyzer
import scoring

AARAV = {
    "branch": "Computer Engineering", "year": "TE", "division": "A",
    "subjects": ["IIS", "TOC", "Computer Graphics", "Microprocessor"],
    "interests": ["Artificial Intelligence", "Machine Learning", "Internships", "Hackathons"],
}
RIYA = {
    "branch": "Mechanical Engineering", "year": "SE", "division": "B",
    "subjects": ["Thermodynamics", "Manufacturing"],
    "interests": ["Design", "Robotics"],
}


def _iis_notice(deadline):
    return {
        "body": "All T.E. Computer Engineering students must submit their IIS journal.",
        "target_branches": ["Computer Engineering"], "target_years": ["TE"],
        "target_divisions": [], "topics": ["IIS"], "interests": [],
        "deadline": deadline, "action_required": True, "mandatory": True,
    }


class TestAnalyzer(unittest.TestCase):
    def test_branch_match(self):
        self.assertIn("Computer Engineering",
                      analyzer.detect_branches("T.E. Computer Engineering students"))

    def test_year_match(self):
        self.assertIn("TE", analyzer.detect_years("All T.E. students must attend"))

    def test_division_match(self):
        self.assertIn("A", analyzer.detect_divisions("Division A students report"))

    def test_deadline_textual(self):
        self.assertEqual(analyzer.detect_deadline("submit by 30 September 2026"),
                         date(2026, 9, 30))

    def test_deadline_numeric(self):
        self.assertEqual(analyzer.detect_deadline("due 30/09/2026"), date(2026, 9, 30))

    def test_missing_deadline(self):
        self.assertIsNone(analyzer.detect_deadline("no date mentioned here"))

    def test_action_and_mandatory(self):
        a = analyzer.analyze_notice("Students must submit the assignment")
        self.assertTrue(a["action_required"])
        self.assertTrue(a["mandatory"])

    def test_unknown_metadata_no_crash(self):
        a = analyzer.analyze_notice("!!! ??? random 123 %%%")
        self.assertEqual(a["target_branches"], [])
        self.assertIsNone(a["deadline"])

    def test_empty_input_no_crash(self):
        a = analyzer.analyze_notice("")
        self.assertEqual(a["category"], "General")


class TestScoring(unittest.TestCase):
    def test_subject_relevance(self):
        rel, _, _ = scoring.calculate_relevance(AARAV, _iis_notice(None))
        self.assertGreaterEqual(rel, 85)

    def test_interest_relevance(self):
        notice = {"body": "AI/ML session", "target_branches": [], "target_years": [],
                  "target_divisions": [], "topics": [],
                  "interests": ["Artificial Intelligence"],
                  "deadline": None, "action_required": False, "mandatory": False}
        rel, _, bd = scoring.calculate_relevance(AARAV, notice)
        self.assertEqual(bd["interest_score"], 15)

    def test_deadline_urgency(self):
        self.assertEqual(scoring.urgency_score((date.today()).isoformat()), 100)
        self.assertEqual(scoring.urgency_score((date.today() + timedelta(days=3)).isoformat()), 85)
        self.assertEqual(scoring.urgency_score(None), 10)

    def test_mandatory_priority(self):
        notice = _iis_notice((date.today() + timedelta(days=1)).isoformat())
        scored = scoring.score_notice_for_user(AARAV, notice)
        self.assertEqual(scored["priority_level"], "HIGH")

    def test_low_relevance_prevents_high(self):
        # Riya on a near-deadline CE-only mandatory notice must NOT be HIGH.
        notice = _iis_notice((date.today()).isoformat())
        scored = scoring.score_notice_for_user(RIYA, notice)
        self.assertEqual(scored["priority_level"], "LOW")
        self.assertLess(scored["priority_score"], 50)

    def test_same_notice_different_students(self):
        notice = _iis_notice((date.today() + timedelta(days=1)).isoformat())
        a = scoring.score_notice_for_user(AARAV, notice)
        r = scoring.score_notice_for_user(RIYA, notice)
        self.assertGreater(a["relevance"], r["relevance"])
        self.assertNotEqual(a["priority_level"], r["priority_level"])

    def test_missing_deadline_no_crash(self):
        scored = scoring.score_notice_for_user(AARAV, _iis_notice(None))
        self.assertEqual(scored["deadline_label"], "No deadline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
