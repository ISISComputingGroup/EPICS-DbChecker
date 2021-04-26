import unittest
import src.db_checker as checker
from src.grouper import RecordGroup


class TestDbChecker(unittest.TestCase):
    test_group = RecordGroup("TEST", "TEST")

    def test_empty(self):
        self.assertIsNotNone(checker.DbChecker(""))

    def test_remove_macro_no_macro(self):
        self.assertEqual(checker.remove_macro("No_Macro"), "No_Macro")

    def test_remove_macro_colon_true(self):
        self.assertEqual(checker.remove_macro("$(P):COLONADDED"), "COLONADDED")

    def test_remove_macro_colon_false(self):
        self.assertEqual(checker.remove_macro("$(P):COLONADDED", False), ":COLONADDED")

    def test_remove_macro_colon_true_no_colon(self):
        self.assertEqual(checker.remove_macro("$(P)COLONADDED", False), "COLONADDED")

    def test_check_case_success(self):
        db = checker.DbChecker("")
        db.check_case("ALL CAPS")
        self.assertFalse(db.errors)

    def test_check_case_failure_some(self):
        db = checker.DbChecker("")
        db.check_case("MOSTLY Caps")
        self.assertEqual(len(db.errors), 1)

    def test_check_case_failure(self):
        db = checker.DbChecker("")
        db.check_case("no caps")
        self.assertEqual(len(db.errors), 1)

    def test_check_chars(self):
        db = checker.DbChecker("")
        db.check_chars("NO_CHARS1:")
        self.assertFalse(db.errors)

    def test_check_chars_numbers_only(self):
        db = checker.DbChecker("")
        db.check_chars("126582084")
        self.assertFalse(db.errors)

    def test_check_chars_alpha_only(self):
        db = checker.DbChecker("")
        db.check_chars("sdhvsnvopsiv")
        self.assertFalse(db.errors)

    def test_check_chars_punc_only(self):
        db = checker.DbChecker("")
        db.check_chars("::__:")
        self.assertFalse(db.errors)

    def test_check_chars_invalid_only(self):
        db = checker.DbChecker("")
        db.check_chars(r"  ///\\\"")
        self.assertEqual(len(db.errors), 1)

    def test_check_chars_invalid(self):
        db = checker.DbChecker("")
        db.check_chars("Contains invalid chars")
        self.assertEqual(len(db.errors), 1)

    def test_check_candidates_read_only(self):
        db = checker.DbChecker("")
        db.check_candidates(self.test_group)
        self.assertFalse(db.errors)

    def test_check_candidates_has_sp_rbv(self):
        db = checker.DbChecker("")
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SP"
        self.test_group.SP_RBV = "TEST:SP:RBV"
        db.check_candidates(self.test_group)
        self.assertFalse(db.errors)

