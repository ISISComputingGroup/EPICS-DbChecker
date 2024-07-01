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
    name_list = ["field1", "field2", "field3", "field4", "field5"]
    value_list = [0, 1, 2, 3, 4]
    field_list = [ec.Field(name_list[0], value_list[0]), ec.Field(name_list[1], value_list[1]),
                  ec.Field(name_list[2], value_list[2]), ec.Field(name_list[3], value_list[3]),
                  ec.Field(name_list[4], value_list[4])]

    def test_is_sim_true(self):
        test_record = ec.Record("test", "ISSIM:1", [], [], [])
        self.assertTrue(test_record.is_sim())

    def test_is_sim_false(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertFalse(test_record.is_sim())

    def test_is_disable_true(self):
        test_record = ec.Record("test", "TEST:DISABLE", [], [], [])
        self.assertTrue(test_record.is_disable())

    def test_is_disable_false(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertFalse(test_record.is_disable())

    def test_field_names_empty(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertFalse(test_record.get_field_names())

    def test_field_names(self):
        test_record = ec.Record("test", "TEST:1", [], self.field_list, [])
        self.assertListEqual(test_record.get_field_names(), self.name_list)

    def test_field_values_empty(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertFalse(test_record.get_field_values())

    def test_field_values(self):
        test_record = ec.Record("test", "TEST:1", [], self.field_list, [])
        self.assertListEqual(test_record.get_field_values(), self.value_list)

    def test_has_field_true(self):
        test_record = ec.Record("test", "TEST:1", [], self.field_list, [])
        self.assertTrue(test_record.has_field(self.name_list[0]))

    def test_has_field_false(self):
        test_record = ec.Record("test", "TEST:1", [], self.field_list, [])
        self.assertFalse(test_record.has_field("fake_field"))

    def test_has_field_empty(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertFalse(test_record.has_field(self.name_list[0]))

    def test_get_field_success(self):
        test_record = ec.Record("test", "TEST:1", [], self.field_list, [])
        self.assertEqual(test_record.get_field_value(self.name_list[0]), self.value_list[0])

    def test_get_field_fail(self):
        test_record = ec.Record("test", "TEST:1", [], self.field_list, [])
        self.assertIsNone(test_record.get_field_value("fake_field"))

    def test_get_field_empty(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertIsNone(test_record.get_field_value(self.name_list[0]))

    def test_get_info_success(self):
        test_record = ec.Record("test", "TEST:1", self.field_list, [], [])
        self.assertEqual(test_record.get_info(self.name_list[0]), self.value_list[0:1])

    def test_get_info_fail(self):
        test_record = ec.Record("test", "TEST:1", self.field_list, [], [])
        self.assertFalse(test_record.get_info("fake_info"))

    def test_get_info_empty(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertFalse(test_record.get_info(self.name_list[0]))

    def test_is_interest_true(self):
        test_record = ec.Record("test", "TEST:1", self.field_list + [ec.Field("INTEREST", 0)], [], [])
        self.assertTrue(test_record.is_interest())

    def test_is_interest_false(self):
        test_record = ec.Record("test", "TEST:1", self.field_list, [], [])
        self.assertFalse(test_record.is_interest())

    def test_is_interest_empty(self):
        test_record = ec.Record("test", "TEST:1", [], [], [])
        self.assertFalse(test_record.is_interest())
