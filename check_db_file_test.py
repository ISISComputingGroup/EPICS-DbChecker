import unittest
from src.db_checker import DbChecker
from os.path import join


# Check that the test files return the same number of errors and warnings as they do in master
class TestWithDBExamples(unittest.TestCase):
    test_folder = "check_db_file_tests"

    def test_examples(self):
        filepath = join(self.test_folder, "examples.db")
        self.run_check(filepath, 15, 0)

    def test_agilent(self):
        filepath = join(self.test_folder, "Agilent_33220A.db")
        self.run_check(filepath, 24, 0)

    def test_fl300(self):
        filepath = join(self.test_folder, "FL300.db")
        self.run_check(filepath, 1, 0)

    def test_isisbeam(self):
        filepath = join(self.test_folder, "isisbeam.db")
        self.run_check(filepath, 0, 0)

    def test_kepco(self):
        filepath = join(self.test_folder, "kepco.db")
        self.run_check(filepath, 0, 2)

    def test_stanford(self):
        filepath = join(self.test_folder, "Stanford_PS350.db")
        self.run_check(filepath, 0, 0)

    def run_check(self, filepath, expected_errors, expected_warnings):
        dbc = DbChecker(filepath, False)
        warnings, errors = dbc.check()
        # Check that the correct number of errors and warnings were found.
        self.assertEqual(errors, expected_errors)
        self.assertEqual(warnings, expected_warnings)
