import unittest
from src.db_checker import DbChecker
from os.path import join


# Check that the test files return the same number of errors and warnings as they do in master
class TestWithDBExamples(unittest.TestCase):
    test_folder = "check_db_file_tests"

    def test_syntax_examples(self):
        filepath = join(self.test_folder, "examples.db")
        self.run_syntax_check(filepath, 1, 14)

    def test_syntax_agilent(self):
        filepath = join(self.test_folder, "Agilent_33220A.db")
        self.run_syntax_check(filepath, 24, 0)

    def test_syntax_fl300(self):
        filepath = join(self.test_folder, "FL300.db")
        self.run_syntax_check(filepath, 0, 1)

    def test_syntax_isisbeam(self):
        filepath = join(self.test_folder, "isisbeam.db")
        self.run_syntax_check(filepath, 0, 0)

    def test_syntax_kepco(self):
        filepath = join(self.test_folder, "kepco.db")
        self.run_syntax_check(filepath, 0, 2)

    def test_syntax_stanford(self):
        filepath = join(self.test_folder, "Stanford_PS350.db")
        self.run_syntax_check(filepath, 0, 0)

    def test_pv_all(self):
        filepath = join(self.test_folder, "test_all.db")
        self.run_pv_check(filepath, 0, 7)

    def test_pv_log_info(self):
        filepath = join(self.test_folder, "test_log_info_errors.db")
        self.run_pv_check(filepath, 0, 2)

    def test_pv_multiple(self):
        filepath = join(self.test_folder, "test_multiple_PVs.db")
        self.run_pv_check(filepath, 1, 0)

    def test_pv_units(self):
        filepath = join(self.test_folder, "test_units.db")
        self.run_pv_check(filepath, 0, 13)

    def run_syntax_check(self, filepath, expected_warnings, expected_errors):
        dbc = DbChecker(filepath, False)
        dbc.parse_db_file()
        warnings, errors = dbc.syntax_check()
        # Check that the correct number of errors and warnings were found.
        print(errors)
        self.assertEqual(errors, expected_errors)
        self.assertEqual(warnings, expected_warnings)

    def run_pv_check(self, filepath, expected_warnings, expected_errors):
        dbc = DbChecker(filepath, False)
        dbc.parse_db_file()
        warnings, errors = dbc.pv_check()
        # Check that the correct number of errors and warnings were found.
        self.assertEqual(errors, expected_errors)
        self.assertEqual(warnings, expected_warnings)
