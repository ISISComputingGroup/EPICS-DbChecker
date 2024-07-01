import unittest
from os.path import join

from src.db_checker import DbChecker
from src.db_parser.lexer import Lexer
from src.db_parser.parser import Parser


# Check that the test files return the same number of errors and warnings as they do in master
class TestWithDBExamples(unittest.TestCase):
    test_folder = "check_db_file_tests"

    def test_syntax_examples(self):
        filepath = join(self.test_folder, "examples.db")
        self.run_syntax_check(
            filepath,
            1,
            [
                "FORMAT ERROR: $(P):COLONADDED should not have a colon after the macro",
                "FORMAT ERROR: $(P)BLAH_BLAH does not have a correctly formatted :SP",
                "FORMAT ERROR: $(P)BLAH_BLAH does not have a correctly formatted :SP:RBV",
                "CHARACTER ERROR: INVALIDCHAR-HERE contains illegal characters",
                "FORMAT ERROR: $(P)PUSHBUTTON_1:SP does not have a correctly named readback alias",
                "PARAMETER ERROR: $(P)SIM:OUTPUT2:STATUS has a :SP but not a :SP:RBV",
                "FORMAT ERROR: $(P)TEMP does not have a correctly formatted :SP:RBV",
                "FORMAT ERROR: $(P)TEMP1 does not have a correctly formatted :SP",
                "FORMAT ERROR: $(P)TEMP1 does not have a correctly formatted :SP:RBV",
                "FORMAT ERROR: $(P)TEST:TEST does not have a correctly formatted :SP",
                "FORMAT ERROR: $(P)TEST:TEST does not have a correctly formatted :SP:RBV",
                "FORMAT ERROR: $(P)Y does not have a correctly formatted :SP",
                "FORMAT ERROR: $(P)Y does not have a correctly formatted :SP:RBV",
                "PARAMETER ERROR: $(P)Z has a :SP but not a :SP:RBV",
            ],
        )

    def test_syntax_agilent(self):
        filepath = join(self.test_folder, "Agilent_33220A.db")
        self.run_syntax_check(filepath, 24, [])

    def test_syntax_fl300(self):
        filepath = join(self.test_folder, "FL300.db")
        self.run_syntax_check(
            filepath, 0, ["PARAMETER ERROR: $(P)MODE has a :SP but not a :SP:RBV"]
        )

    def test_syntax_isisbeam(self):
        filepath = join(self.test_folder, "isisbeam.db")
        self.run_syntax_check(filepath, 0, [])

    def test_syntax_kepco(self):
        filepath = join(self.test_folder, "kepco.db")
        self.run_syntax_check(
            filepath,
            0,
            [
                "PARAMETER ERROR: $(P)CURRENT has a :SP but not a :SP:RBV",
                "PARAMETER ERROR: $(P)VOLTAGE has a :SP but not a :SP:RBV",
            ],
        )

    def test_syntax_stanford(self):
        filepath = join(self.test_folder, "Stanford_PS350.db")
        self.run_syntax_check(filepath, 0, [])

    def test_pv_all(self):
        filepath = join(self.test_folder, "test_all.db")
        self.run_pv_check(
            filepath,
            [],
            [
                "Missing description on SHOULDFAIL:NODESC",
                "Invalid unit 'BADUNIT' on SHOULDFAIL:BADUNIT",
                "Description too long on SHOULDFAIL:LONGDESC",
                "Missing ASG on SHOULDFAIL:CALCNOREADONLY",
                "Missing units on SHOULDFAIL:NOUNITS",
                "Multiple instances of fields EGU on SHOULDFAIL:DUPLICATE:EGU",
                "Multiple instances of fields PINI on SHOULDFAIL:DUPLICATE:PINI",
            ],
        )

    def test_pv_log_info(self):
        filepath = join(self.test_folder, "test_log_info_errors.db")
        self.run_pv_check(
            filepath,
            [],
            [
                "Invalid logging config: SHOULDFAIL:HEADER_REPEAT repeats the log info tag log_header1",
                "Invalid logging config: SHOULDFAIL:LOGGING_PERIOD_REDEFINE alters the logging period type",
            ],
        )

    def test_pv_multiple(self):
        filepath = join(self.test_folder, "test_multiple_PVs.db")
        self.run_pv_check(filepath, ["Multiple instances of SHOULDPASS:MULTIPLEWARNING"], [])

    def test_pv_units(self):
        filepath = join(self.test_folder, "test_units.db")
        self.run_pv_check(
            filepath,
            [],
            [
                "Invalid unit 'bit kbyte^-1' on SHOULDFAIL:BITS_KBYTE^-1",
                "Invalid unit 'm^-1' on SHOULDFAIL:M-1",
                "Invalid unit 'm s^-1' on SHOULDFAIL:m_S-1",
                "Invalid unit 'kkm' on SHOULDFAIL:BADUNIT:KKM",
                "Invalid unit 'kmk' on SHOULDFAIL:BADUNIT:KMK",
                "Invalid unit 'k/(m s)' on SHOULDFAIL:BADUNIT:KM-1_S-1",
                "Invalid unit 'm/(As)' on SHOULDFAIL:BADUNIT:MA-1S-1",
                "Invalid unit 'dm' on SHOULDFAIL:BADUNIT:DM",
                "Invalid unit 'kM' on SHOULDFAIL:BADUNIT:CAPS",
                "Invalid unit 'Km' on SHOULDFAIL:BADUNIT:CAPS_2",
                "Invalid unit '1' on SHOULDFAIL:BADUNIT:1",
                "Invalid unit 'm^-2' on SHOULDFAIL:BADUNIT:negative_square_power",
                "Invalid unit 'm^-1' on SHOULDFAIL:BADUNIT:negative_power",
            ],
        )

    def run_syntax_check(self, filepath, expected_warnings, expected_errors):
        self.maxDiff = 1500
        with open(filepath) as f:
            parsed_db = Parser(Lexer(f.read())).db()
        dbc = DbChecker(parsed_db, filepath, True)
        warnings, errors = dbc.syntax_check()
        # Check that the correct number of errors and warnings were found.
        self.assertListEqual(errors, expected_errors)
        self.assertEqual(warnings, expected_warnings)

    def run_pv_check(self, filepath, expected_warnings, expected_errors):
        with open(filepath) as f:
            parsed_db = Parser(Lexer(f.read())).db()
        dbc = DbChecker(parsed_db, filepath, True)
        warnings, errors = dbc.pv_check()
        # Check that the correct number of errors and warnings were found.
        self.assertListEqual(errors, expected_errors)
        self.assertEqual(warnings, expected_warnings)
