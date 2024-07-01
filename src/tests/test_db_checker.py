import unittest

import src.db_checker as checker
from src.db_parser.EPICS_collections import Record
from src.grouper import RecordGroup


class TestDbChecker(unittest.TestCase):
    def test_empty(self):
        self.assertIsNotNone(checker.DbChecker("", ""))

    def test_remove_macro_no_macro(self):
        self.assertEqual(checker.remove_macro("No_Macro"), "No_Macro")

    def test_remove_macro_colon_true(self):
        self.assertEqual(checker.remove_macro("$(P):COLONADDED"), "COLONADDED")

    def test_remove_macro_colon_true_no_colon(self):
        self.assertEqual(checker.remove_macro("$(P)COLONADDED", True), "COLONADDED")

    def test_remove_macro_colon_false(self):
        self.assertEqual(checker.remove_macro("$(P):COLONADDED", False), ":COLONADDED")

    def test_remove_macro_colon_false_no_colon(self):
        self.assertEqual(checker.remove_macro("$(P)COLONADDED", False), "COLONADDED")

    def test_check_case_success(self):
        db = checker.DbChecker("", "")
        db.check_case("ALL CAPS")

        self.assertFalse(db.catch)

    def test_check_case_failure_some(self):
        db = checker.DbChecker("", "")
        db.check_case("MOSTLY Caps")

        self.assertEqual(len(db.warnings), 1)

    def test_check_case_failure(self):
        db = checker.DbChecker("", "")
        db.check_case("no caps")

        self.assertEqual(len(db.warnings), 1)

    def test_check_chars(self):
        db = checker.DbChecker("", "")
        db.check_chars("NO_CHARS1:")

        self.assertFalse(db.catch)

    def test_check_chars_numbers_only(self):
        db = checker.DbChecker("", "")
        db.check_chars("126582084")

        self.assertFalse(db.catch)

    def test_check_chars_alpha_only(self):
        db = checker.DbChecker("", "")
        db.check_chars("sdhvsnvopsiv")

        self.assertFalse(db.catch)

    def test_check_chars_punc_only(self):
        db = checker.DbChecker("", "")
        db.check_chars("::__:")

        self.assertFalse(db.catch)

    def test_check_chars_invalid_only(self):
        db = checker.DbChecker("", "")
        db.check_chars(r"  ///\\\"")

        self.assertEqual(len(db.catch), 1)

    def test_check_chars_invalid(self):
        db = checker.DbChecker("", "")
        db.check_chars("Contains invalid chars")

        self.assertEqual(len(db.catch), 1)


# Separate class because needs these variables reset between tests
class TestDbCheckerWithRecords(unittest.TestCase):
    def setUp(self):
        self.test_group = RecordGroup("TEST", "TEST")
        self.record_dict = {"TEST": Record("", "TEST", [], [], []), "TEST:SP": Record("", "TEST:SP", [], [], []),
                            "TEST:SP:RBV": Record("", "TEST:SP:RBV", [], [], [])}

    def test_check_candidates_fail_sp_no_rb(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.SP = "TEST:SP"
        self.test_group.main = self.test_group.SP
        self.test_group.SP_RBV = "TEST:SP:RBV"

        db.check_candidates(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_check_candidates_fail_rbv_main(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.SP_RBV = "TEST:SP:RBV"
        self.test_group.main = self.test_group.SP_RBV

        db.check_candidates(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_sp_main_checks_fail_sp_no_rb(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.SP = "TEST:SP"
        self.test_group.main = self.test_group.SP

        db.sp_main_checks(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_sp_main_checks_fail_sp_main_rb_not_alias(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SP"
        self.test_group.main = self.test_group.SP

        db.sp_main_checks(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_sp_main_checks_success_sp_main_rb_alias(self):
        db = checker.DbChecker("", "")
        self.record_dict["TEST:SP"].aliases.append("TEST")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SP"
        self.test_group.main = self.test_group.SP

        db.sp_main_checks(self.test_group)

        self.assertFalse(db.catch)

    def test_check_candidates_read_only(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"

        db.check_candidates(self.test_group)

        self.assertFalse(db.catch)

    def test_check_readback_read_only(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"

        db.check_readback(self.test_group)

        self.assertFalse(db.catch)

    def test_check_readback_has_sp_rbv(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SP"
        self.test_group.SP_RBV = "TEST:SP:RBV"

        db.check_readback(self.test_group)

        self.assertFalse(db.catch)

    def test_check_readback_fail_rbv_no_sp(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP_RBV = "TEST:SP:RBV"

        db.check_readback(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_check_readback_fail_sp_no_rbv(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SP"

        db.check_readback(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_check_readback_fail_sp_bad_format(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SETPOINT"
        self.test_group.SP_RBV = "TEST:SP:RBV"

        db.check_readback(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_check_readback_fail_RBV_bad_format(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SP"
        self.test_group.SP_RBV = "TEST:SETPOINT:READBACK"

        db.check_readback(self.test_group)

        self.assertEqual(len(db.catch), 1)

    def test_check_readback_fail_bad_format(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SETPOINT"
        self.test_group.SP_RBV = "TEST:SETPOINT:READBACK"

        db.check_readback(self.test_group)

        self.assertEqual(len(db.catch), 2)

    def test_check_sp_format_fail_rbv(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP_RBV = "TEST:SETPOINT:READBACK"

        db.check_sp_formatting(":SP:RBV", self.test_group, self.test_group.SP_RBV)

        self.assertEqual(len(db.catch), 1)

    def test_check_sp_format_fail_sp(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SETPOINT"

        db.check_sp_formatting(":SP", self.test_group, self.test_group.SP)

        self.assertEqual(len(db.catch), 1)

    def test_check_sp_format_success(self):
        db = checker.DbChecker("", "")
        db.records_dict = self.record_dict
        self.test_group.RB = "TEST"
        self.test_group.SP = "TEST:SP"

        db.check_sp_formatting(":SP", self.test_group, self.test_group.SP)

        self.assertFalse(db.catch)
