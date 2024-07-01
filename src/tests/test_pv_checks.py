import unittest

import src.db_parser.EPICS_collections as Ec
import src.pv_checks as pv


class PvChecksTest(unittest.TestCase):
    record_name_list = ["record1", "record2", "record3", "record4", "record5"]
    record_list = [
        Ec.Record("type", record_name_list[0], [], [], []),
        Ec.Record("type", record_name_list[1], [], [], []),
        Ec.Record("type", record_name_list[2], [], [], []),
        Ec.Record("type", record_name_list[3], [], [], []),
        Ec.Record("type", record_name_list[4], [], [], []),
    ]

    field_name_list = ["field1", "field2", "field3", "field4", "field5"]
    value_list = [0, 1, 2, 3, 4]
    field_list = [
        Ec.Field(field_name_list[0], value_list[0]),
        Ec.Field(field_name_list[1], value_list[1]),
        Ec.Field(field_name_list[2], value_list[2]),
        Ec.Field(field_name_list[3], value_list[3]),
        Ec.Field(field_name_list[4], value_list[4]),
    ]

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

    def test_get_multiple_instances_empty(self):
        test_db = Ec.Db("path", [])
        self.assertFalse(pv.get_multiple_instances(test_db))

    def test_get_multiple_instances_no(self):
        test_db = Ec.Db("path", self.record_list)
        self.assertFalse(pv.get_multiple_instances(test_db))

    def test_get_multiple_instances_1(self):
        test_db = Ec.Db(
            "path", self.record_list + [Ec.Record("type", self.record_name_list[0], [], [], [])]
        )
        self.assertEqual(len(pv.get_multiple_instances(test_db)), 1)

    def test_get_multiple_instances_more(self):
        test_db = Ec.Db(
            "path",
            self.record_list + (5 * [Ec.Record("type", self.record_name_list[0], [], [], [])]),
        )
        self.assertEqual(len(pv.get_multiple_instances(test_db)), 1)

    def test_get_multiple_properties_on_pvs_empty(self):
        test_db = Ec.Db("path", self.record_list)
        self.assertFalse(pv.get_multiple_properties_on_pvs(test_db))

    def test_get_multiple_properties_on_pvs_no(self):
        diff_records = [
            Ec.Record("type", name, [], self.field_list, []) for name in self.record_name_list
        ]

        test_db = Ec.Db("path", diff_records)
        self.assertFalse(pv.get_multiple_properties_on_pvs(test_db))

    def test_get_multiple_properties_on_pvs_yes(self):
        diff_records = [
            Ec.Record("type", self.record_name_list[0], [], self.field_list + self.field_list, [])
        ]
        test_db = Ec.Db("path", diff_records)
        self.assertEqual(len(pv.get_multiple_properties_on_pvs(test_db)), 1)

    def test_get_multiple_properties_on_pvs_yes_across_multiple(self):
        diff_records = [
            Ec.Record("type", name, [], self.field_list + self.field_list, [])
            for name in self.record_name_list
        ]
        test_db = Ec.Db("path", diff_records)
        self.assertEqual(len(pv.get_multiple_properties_on_pvs(test_db)), len(diff_records))

    def test_get_interest_units_empty_info(self):
        test_db = Ec.Db(
            "path", [Ec.Record("longin", self.record_name_list[0], [], self.field_list, [])]
        )
        self.assertFalse(pv.get_interest_units(test_db))

    def test_get_interest_units_not_interesting(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [
                Ec.Record(
                    "longin", self.record_name_list[0], [Ec.Field("BORING", 0)], self.field_list, []
                )
            ],
        )
        self.assertFalse(pv.get_interest_units(test_db))

    def test_get_interest_units_interesting_success(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "longin",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    self.field_list + [Ec.Field("EGU", "bit/kbyte")],
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_units(test_db))

    def test_get_interest_units_interesting_success_out(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "longout",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    self.field_list + [Ec.Field("EGU", "bit/kbyte")],
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_units(test_db))

    def test_get_interest_units_interesting_success_ai(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "ai",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    self.field_list + [Ec.Field("EGU", "bit/kbyte")],
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_units(test_db))

    def test_get_interest_units_interesting_success_ao(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "ao",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    self.field_list + [Ec.Field("EGU", "bit/kbyte")],
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_units(test_db))

    def test_get_interest_units_interesting_mult_success(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "longin",
                    name,
                    [Ec.Field("INTEREST", 0)],
                    self.field_list + [Ec.Field("EGU", "bit/kbyte")],
                    [],
                )
                for name in self.record_name_list
            ],
        )
        self.assertFalse(pv.get_interest_units(test_db))

    def test_get_interest_units_interesting_fail(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "longin",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertEqual(len(pv.get_interest_units(test_db)), 1)

    def test_get_interest_units_interesting_fail_out(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "longout",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertEqual(len(pv.get_interest_units(test_db)), 1)

    def test_get_interest_units_interesting_fail_ai(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "ai", self.record_name_list[0], [Ec.Field("INTEREST", 0)], self.field_list, []
                )
            ],
        )
        self.assertEqual(len(pv.get_interest_units(test_db)), 1)

    def test_get_interest_units_interesting_fail_ao(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "ao", self.record_name_list[0], [Ec.Field("INTEREST", 0)], self.field_list, []
                )
            ],
        )
        self.assertEqual(len(pv.get_interest_units(test_db)), 1)

    def test_get_interest_units_interesting_mult_fail(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record("longin", name, [Ec.Field("INTEREST", 0)], self.field_list, [])
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_interest_units(test_db)), len(self.record_name_list))

    def test_get_interest_calc_readonly_empty_info(self):
        test_db = Ec.Db(
            "path", [Ec.Record("calc", self.record_name_list[0], [], self.field_list, [])]
        )
        self.assertFalse(pv.get_interest_calc_readonly(test_db))

    def test_get_interest_calc_readonly_not_interesting(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [
                Ec.Record(
                    "calc",
                    self.record_name_list[0],
                    [Ec.Field("BORING", 0)],
                    [Ec.Field("ASG", "NOTREADONLY")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_calc_readonly(test_db))

    def test_get_interest_calc_readonly_not_asg(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [
                Ec.Record(
                    "notcalc",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    [Ec.Field("ASG", "NOTREADONLY")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_calc_readonly(test_db))

    def test_get_interest_calc_readonly_fail(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [
                Ec.Record(
                    "calc",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    [Ec.Field("ASG", "NOTREADONLY")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertEqual(len(pv.get_interest_calc_readonly(test_db)), 1)

    def test_get_interest_calc_readonly_fail_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "calc",
                    name,
                    [Ec.Field("INTEREST", 0)],
                    [Ec.Field("ASG", "NOTREADONLY")] + self.field_list,
                    [],
                )
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_interest_calc_readonly(test_db)), len(self.record_name_list))

    def test_get_interest_calc_readonly_success(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [
                Ec.Record(
                    "calc",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    [Ec.Field("ASG", "READONLY")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_calc_readonly(test_db))

    def test_get_interest_calc_readonly_success_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "calc",
                    name,
                    [Ec.Field("INTEREST", 0)],
                    [Ec.Field("ASG", "READONLY")] + self.field_list,
                    [],
                )
                for name in self.record_name_list
            ],
        )
        self.assertFalse(pv.get_interest_calc_readonly(test_db))

    def test_get_desc_length_empty(self):
        test_db = Ec.Db("path", self.record_list)
        self.assertFalse(pv.get_desc_length(test_db))

    def test_get_desc_length_no_desc(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [Ec.Record("type", self.record_name_list[0], [], self.field_list, [])],
        )
        self.assertFalse(pv.get_desc_length(test_db))

    def test_get_desc_length_success(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [],
                    self.field_list + [Ec.Field("DESC", "Short")],
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_desc_length(test_db))

    def test_get_desc_length_success_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record("type", name, [], self.field_list + [Ec.Field("DESC", "Short")], [])
                for name in self.record_name_list
            ],
        )
        self.assertFalse(pv.get_desc_length(test_db))

    def test_get_desc_length_fail(self):
        test_db = Ec.Db(
            "path",
            self.record_list
            + [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [],
                    self.field_list + [Ec.Field("DESC", 41 * "0")],
                    [],
                )
            ],
        )
        self.assertEqual(len(pv.get_desc_length(test_db)), 1)

    def test_get_desc_length_fail_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record("type", name, [], self.field_list + [Ec.Field("DESC", 41 * "0")], [])
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_desc_length(test_db)), len(self.record_name_list))

    def test_get_units_valid_empty(self):
        test_db = Ec.Db("path", self.record_list)
        self.assertFalse(pv.get_units_valid(test_db))

    def test_get_units_valid_no_units(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [],
                    [Ec.Field("ASG", "NOTREADONLY")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_units_valid(test_db))

    def test_get_units_valid_fail(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [],
                    [Ec.Field("EGU", "NOTUNIT")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertEqual(len(pv.get_units_valid(test_db)), 1)

    def test_get_units_valid_fail_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record("type", name, [], [Ec.Field("EGU", "NOTUNIT")] + self.field_list, [])
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_units_valid(test_db)), len(self.record_name_list))

    def test_get_units_valid_blank(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [],
                    [Ec.Field("EGU", "")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_units_valid(test_db))

    def test_get_units_valid_success(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [],
                    [Ec.Field("EGU", "cm")] + self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_units_valid(test_db))

    def test_get_units_valid_success_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record("type", name, [], [Ec.Field("EGU", "cm")] + self.field_list, [])
                for name in self.record_name_list
            ],
        )
        self.assertFalse(pv.get_units_valid(test_db))

    def test_get_interest_descriptions_empty(self):
        test_db = Ec.Db("path", self.record_list)
        self.assertFalse(pv.get_interest_descriptions(test_db))

    def test_get_interest_descriptions_not_interest(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [Ec.Field("NOTINTEREST", 0)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_descriptions(test_db))

    def test_get_interest_descriptions_fail_single(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type", self.record_name_list[0], [Ec.Field("INTEREST", 0)], self.field_list, []
                )
            ],
        )
        self.assertEqual(len(pv.get_interest_descriptions(test_db)), 1)

    def test_get_interest_descriptions_fail_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record("type", name, [Ec.Field("INTEREST", 0)], self.field_list, [])
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_interest_descriptions(test_db)), len(self.record_name_list))

    def test_get_interest_descriptions_success_single(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    [Ec.Field("INTEREST", 0)],
                    self.field_list + [Ec.Field("DESC", "Short")],
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_interest_descriptions(test_db))

    def test_get_interest_descriptions_success_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    name,
                    [Ec.Field("INTEREST", 0)],
                    self.field_list + [Ec.Field("DESC", "Short")],
                    [],
                )
                for name in self.record_name_list
            ],
        )
        self.assertFalse(pv.get_interest_descriptions(test_db))

    def test_get_log_info_tags_empty(self):
        test_db = Ec.Db("path", self.record_list)
        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_no_logs(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record("type", name, self.field_list, self.field_list, [])
                for name in self.record_name_list
            ],
        )
        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_success_single_log(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    self.field_list + [Ec.Field("log_test", 0)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_success_multi_log(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    name,
                    self.field_list + [Ec.Field("log_test_{}".format(name), 0)],
                    self.field_list,
                    [],
                )
                for name in self.record_name_list
            ],
        )

        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_fail_multi_log_db(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type", name, self.field_list + [Ec.Field("log_test", 0)], self.field_list, []
                )
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_log_info_tags(test_db)), len(self.record_name_list) - 1)

    def test_get_log_info_tags_fail_multi_log_record(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    name,
                    self.field_list
                    + [
                        Ec.Field("log_test_{}".format(name), 0),
                        Ec.Field("log_test_{}".format(name), 0),
                    ],
                    self.field_list,
                    [],
                )
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_log_info_tags(test_db)), len(self.record_name_list))

    def test_get_log_info_tags_success_single_period(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    self.field_list + [Ec.Field("log_period_seconds", 1)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_success_single_period_pv(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    self.field_list + [Ec.Field("log_period_pv", 1)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_success_single_period_log(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    self.field_list + [Ec.Field("test_log", 0), Ec.Field("log_period_pv", 1)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_success_multi_period_log(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    self.field_list + [Ec.Field("test_log", 0), Ec.Field("log_period_pv", 1)],
                    self.field_list,
                    [],
                ),
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    self.field_list + [Ec.Field("test_log_1", 0)],
                    self.field_list,
                    [],
                ),
            ],
        )
        self.assertFalse(pv.get_log_info_tags(test_db))

    def test_get_log_info_tags_fail_redefine(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    self.record_name_list[0],
                    self.field_list
                    + [Ec.Field("log_period_pv", 1), Ec.Field("log_period_seconds", 2)],
                    self.field_list,
                    [],
                )
            ],
        )
        self.assertEqual(len(pv.get_log_info_tags(test_db)), 1)

    def test_get_log_info_tags_fail_redefine_multi(self):
        test_db = Ec.Db(
            "path",
            [
                Ec.Record(
                    "type",
                    name,
                    self.field_list + [Ec.Field("log_period_pv", 1)],
                    self.field_list,
                    [],
                )
                for name in self.record_name_list
            ],
        )
        self.assertEqual(len(pv.get_log_info_tags(test_db)), 8)
