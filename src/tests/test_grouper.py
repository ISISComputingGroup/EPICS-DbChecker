import unittest

import src.db_parser.EPICS_collections as Ec
import src.grouper as g


class GrouperTest(unittest.TestCase):
    record_name_list = ["TEMP", "TEMP:SP", "TEMP:SP:RBV", "NOTTEMP", "NOTTEMP:SP:RBV"]
    record_dict = {
        record_name_list[0]: Ec.Record("type", record_name_list[0], [], [], []),
        record_name_list[1]: Ec.Record("type", record_name_list[1], [], [], []),
        record_name_list[2]: Ec.Record("type", record_name_list[2], [], [], []),
        record_name_list[3]: Ec.Record("type", record_name_list[3], [], [], []),
        record_name_list[4]: Ec.Record("type", record_name_list[4], [], [], []),
    }

    def test_find_related_type_empty(self):
        result1, result2 = g.find_related_type("", "")

        self.assertIsNone(result1)
        self.assertIsNone(result2)

    def test_find_related_type_not_matching_name(self):
        result1, result2 = g.find_related_type("NOTTEMP:SP", "TEMP")

        self.assertIsNone(result1)
        self.assertIsNone(result2)

    def test_find_related_type_same_name(self):
        result1, result2 = g.find_related_type("TEMP", "TEMP")

        self.assertIsNone(result1)
        self.assertIsNone(result2)

    def test_find_related_type_match_first(self):
        result1, result2 = g.find_related_type("TEMP:SP", "TEMP")

        self.assertIsNotNone(result1)
        self.assertIsNone(result2)

    def test_find_related_type_match_second(self):
        result1, result2 = g.find_related_type("TEMP:SP:RB", "TEMP")

        self.assertIsNone(result1)
        self.assertIsNotNone(result2)

    def test_find_record_type_RB(self):
        grouper = g.Grouper()
        name = "TEMP"

        grouper.find_record_type(name)

        self.assertIn(name, grouper.record_groups)
        self.assertEqual(grouper.record_groups[name].stem, name)
        self.assertEqual(grouper.record_groups[name].main, name)
        self.assertEqual(grouper.record_groups[name].RB, name)

    def test_find_record_type_SP(self):
        grouper = g.Grouper()
        stem = "TEMP"
        name = "TEMP:SP"

        grouper.find_record_type(name)

        self.assertIn(stem, grouper.record_groups)
        self.assertEqual(grouper.record_groups[stem].stem, stem)
        self.assertEqual(grouper.record_groups[stem].main, name)
        self.assertEqual(grouper.record_groups[stem].SP, name)

    def test_find_record_type_RBV(self):
        grouper = g.Grouper()
        stem = "TEMP"
        name = "TEMP:SP:RBV"

        grouper.find_record_type(name)

        self.assertIn(stem, grouper.record_groups)
        self.assertEqual(grouper.record_groups[stem].stem, stem)
        self.assertEqual(grouper.record_groups[stem].main, name)
        self.assertEqual(grouper.record_groups[stem].SP_RBV, name)

    def test_find_record_type_skip_repeated_stem(self):
        grouper = g.Grouper()
        name_sp = "TEMP:SP"
        name_sp_rbv = "TEMP:SP:RBV"

        grouper.find_record_type(name_sp)
        one_item = len(grouper.record_groups)
        grouper.find_record_type(name_sp_rbv)

        self.assertEqual(one_item, len(grouper.record_groups))

    # Slightly different execution for names and stems
    def test_find_record_type_skip_repeated_name(self):
        grouper = g.Grouper()
        name_sp = "TEMP:SP"
        name = "TEMP"

        grouper.find_record_type(name_sp)
        one_item = len(grouper.record_groups)
        grouper.find_record_type(name)

        self.assertEqual(len(grouper.record_groups), one_item)

    def test_group_records_empty(self):
        grouper = g.Grouper()

        print("Test Group Records Empty")
        grouper.group_records({})

        self.assertFalse(grouper.record_groups)

    def test_group_records(self):
        grouper = g.Grouper()

        print("Test Group Records")
        grouper.group_records(self.record_dict, True)

        self.assertEqual(len(grouper.record_groups), 2)
        self.assertEqual(grouper.record_groups["TEMP"].stem, "TEMP")
        self.assertEqual(grouper.record_groups["TEMP"].main, "TEMP")
        self.assertEqual(grouper.record_groups["TEMP"].SP, "TEMP:SP")
        self.assertEqual(grouper.record_groups["TEMP"].SP_RBV, "TEMP:SP:RBV")
        self.assertEqual(grouper.record_groups["NOTTEMP"].stem, "NOTTEMP")
        self.assertEqual(grouper.record_groups["NOTTEMP"].main, "NOTTEMP")
        self.assertEqual(grouper.record_groups["NOTTEMP"].SP_RBV, "NOTTEMP:SP:RBV")

    def test_group_records_aliases(self):
        grouper = g.Grouper()
        tempalias = "TEMPALIAS"
        self.record_dict[tempalias] = Ec.Record(
            "type", tempalias, [], [], ["TEMPALIAS:SP", "TEMPALIAS:SP:RBV"]
        )

        print("Test Aliases 1")
        grouper.group_records(self.record_dict, True)

        self.assertEqual(len(grouper.record_groups), 3)
        self.assertEqual(grouper.record_groups[tempalias].stem, tempalias)
        self.assertEqual(grouper.record_groups[tempalias].main, tempalias)
        self.assertEqual(grouper.record_groups[tempalias].SP, "TEMPALIAS:SP")
        self.assertEqual(grouper.record_groups[tempalias].SP_RBV, "TEMPALIAS:SP:RBV")

    def test_group_records_aliases_SP(self):
        grouper = g.Grouper()
        tempalias = "TEMPALIAS"
        self.record_dict["TEMPALIAS:SP"] = Ec.Record(
            "type", "TEMPALIAS:SP", [], [], ["TEMPALIAS", "TEMPALIAS:SP:RBV"]
        )

        print("Test Aliases 2")
        grouper.group_records(self.record_dict, True)

        self.assertEqual(len(grouper.record_groups), 3)
        self.assertEqual(grouper.record_groups[tempalias].stem, tempalias)
        self.assertEqual(grouper.record_groups[tempalias].main, tempalias)
        self.assertEqual(grouper.record_groups[tempalias].SP, "TEMPALIAS:SP")
        self.assertEqual(grouper.record_groups[tempalias].SP_RBV, "TEMPALIAS:SP:RBV")
