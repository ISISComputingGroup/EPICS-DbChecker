import unittest
import src.pv_checks as pv
import src.db_parser.EPICS_collections as Ec


class PvChecksTest(unittest.TestCase):
    name_list = ["record1", "record2", "record3", "record4", "record5"]
    record_list = [Ec.Record("", name_list[0], [], [], []), Ec.Record("", name_list[1], [], [], []),
                   Ec.Record("", name_list[2], [], [], []), Ec.Record("", name_list[3], [], [], []),
                   Ec.Record("", name_list[4], [], [], [])]

    def test_allowed_unit_standalone(self):
        # only two cases so can easily check both
        self.assertTrue(pv.allowed_unit("cdeg/ss"))
        self.assertTrue(pv.allowed_unit("uA hour"))

    def test_allowed_unit_over(self):
        # check properly handles unit over other unit
        self.assertTrue(pv.allowed_unit("bit/kbyte"))

    def test_allowed_unit_1_over(self):
        # check properly handles 1 over unit
        self.assertTrue(pv.allowed_unit("1/cm"))

    def test_allowed_unit_compound_over(self):
        # check properly handles unit over compound unit
        self.assertTrue(pv.allowed_unit("km/(m s)"))

    def test_allowed_unit_wrong_format_ms(self):
        self.assertTrue(pv.allowed_unit("m/s"))
        self.assertFalse(pv.allowed_unit("m s^-1"))

    def test_allowed_unit_bad_unit(self):
        # properly fails invalid unit
        self.assertFalse(pv.allowed_unit("not a unit"))

    def test_allowed_unit_bad_unit_over(self):
        self.assertFalse(pv.allowed_unit("k / (m s)"))

    def test_allowed_unit_catch_capitals(self):
        self.assertFalse(pv.allowed_unit("M"))

    def test_allowed_unit_wrong_format_1m2(self):
        self.assertTrue(pv.allowed_unit("1 / m ^ 2"))
        self.assertFalse(pv.allowed_unit("m^-2"))

    # need to know some valid macros of units to test that portion of allow units

    def get_multiple_instances_empty(self):
        test_db = Ec.Db("", [])
        self.assertEqual(len(pv.get_multible_instances(test_db)), 0)

    def get_multiple_instances_no(self):
        test_db = Ec.Db("", self.record_list)
        self.assertEqual(len(pv.get_multible_instances(test_db)), 0)

    def get_multiple_instances_1(self):
        test_db = Ec.Db("", self.record_list+[Ec.Record("", self.name_list[0], [], [], [])])
        self.assertEqual(len(pv.get_multible_instances(test_db)), 1)

    def get_multiple_instances_more(self):
        test_db = Ec.Db("", self.record_list+(5*[Ec.Record("", self.name_list[0], [], [], [])]))
        self.assertEqual(len(pv.get_multible_instances(test_db)), 5)
