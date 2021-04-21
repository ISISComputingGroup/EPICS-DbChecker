import unittest
import src.db_parser.EPICS_collections as ec


class TestDBs(unittest.TestCase):
    def test_db_len_empty(self):
        self.run_db_len_check([])

    def test_db_len_1(self):
        self.run_db_len_check([ec.Record("rec_type", "pv", [], [], [])])

    def test_db_len_longer(self):
        self.run_db_len_check([ec.Record("rec_type", "pv", [], [], []),
                               ec.Record("rec_type", "pv2", [], [], []),
                               ec.Record("rec_type", "pv3", [], [], [])])

    def run_db_len_check(self, record):
        db = ec.Db("", record)
        self.assertEqual(len(db), len(record))

class TestRecords(unittest.TestCase):
    def test_is_sim_true(self):

    def test_is_sim_false(self):

    def test_is_disable_true(self):

    def test_is_disable_false(self):

    def test_field_names_empty(self):

    def test_field_names(self):

    def test_field_values_empty(self):

    def test_field_values(self):

    def test_has_field_true(self):

    def test_has_field_false(self):

    def test_has_field_empty(self):

    def test_get_field_success(self):

    def test_get_field_fail(self):

    def test_get_field_empty(self):

    def test_get_info_success(self):

    def test_get_info_fail(self):

    def test_get_info_empty(self):

    def test_is_interest_true(self):

    def test_is_interest_false(self):

