import re

from src.db_parser.lexer import Lexer
from src.db_parser.parser import Parser
from src.grouper import Grouper
from src.pv_checks import run_pv_checks
from src.db_parser.common import DbSyntaxError

# Rules implemented:
# 1) Name should be uppercase
# 2) Colons are used as main separator
# 3) Names only use alphanumerics, underscore and colon
# 4) Adheres to :SP and SP:RBV format
# 5) If DUMMYPV and DUMMYPV:SP exists then DUMMYPV:SP:RBV should exist too
# (DUMMYPV:SP:RBV might be an alias).
# 6) If DUMMYPV:SP exists on its own that is okay - it is probably a push button
# who's status cannot be read, but it should have a SP:RBV alias for DUMMYPV
# 7) If DUMMYPV exists on its own it is okay (represents a read-only parameter)
# 8) Underscores:
#        a) Allowed if used for making a name clearer, e.g. X_POSITION
#        b) Not allowed to use the underscore instead of a ':',
#        e.g. DUMMYPV_SP_RB


def remove_macro(pvname, remove_colon=True):
    if pvname.find('$') != -1:
        left = pvname.rfind(')') + 1
        pvname = pvname[left:]
        # Remove leading : if there is one
        if remove_colon and pvname.startswith(':'):
            pvname = pvname[1:]
    return pvname


class DbChecker:
    def __init__(self, filename, debug=False):
        self.filename = filename
        self.errors = []
        self.warnings = []
        self.catch = []
        self.debug = debug
        self.file = None
        self.parsed_db = None
        self.records_dict = {}

    # handles this separately so we can set a parsed_db manually for unit tests.
    def parse_db_file(self):
        try:
            self.file = open(self.filename)
            self.parsed_db = Parser(Lexer(self.file.read())).db()
            self.file.close()
        except Exception as e:
            print("Error occured with file {}".format(self.filename))
            raise e

    def pv_check(self):
        print("\n** CHECKING {}'s PVs **".format(self.filename))
        warnings, errors = run_pv_checks(self.parsed_db)
        print("**  PV ERROR COUNT = {} **".format(errors))
        print("**  PV WARNING COUNT = {} **".format(warnings))
        return warnings, errors

    def syntax_check(self, strict=False):
        print("\n** CHECKING {}'s Syntax **".format(self.filename))
        grouper = Grouper()
        # Check for consistency in whether PV macros are followed by colons
        self.check_macro_syntax()
        record_names = [record.pv for record in self.parsed_db.records]
        self.records_dict = {name: record for name, record in zip(record_names, self.parsed_db.records)}
        groups = grouper.group_records(self.records_dict)
        if self.debug:
            for group_name in groups.keys():
                print(group_name, groups[group_name].RB, groups[group_name].SP, groups[group_name].SP_RBV)
        for group_name in groups.keys():
            [self.check_case(name) for name in groups[group_name].get_all()]
            [self.check_chars(name) for name in groups[group_name].get_all()]
            self.check_candidates(groups[group_name])
        if strict:
            self.errors = self.catch
        else:
            self.warnings += self.catch
        for w in self.warnings:
            print(w)

        for e in self.errors:
            print(e)

        print("** WARNING COUNT = {} **".format(len(self.warnings)))
        print("** ERROR COUNT = {} **".format(len(self.errors)))

        return len(self.warnings), len(self.errors)

    def check_macro_syntax(self):
        colon = None
        for r in self.parsed_db.records:
            if colon is None:
                n = remove_macro(r.pv, False)
                colon = n.startswith(':')
            else:
                n = remove_macro(r.pv, False)
                if n.startswith(':') != colon:
                    if colon:
                        self.catch.append(
                            "FORMAT ERROR: " + r.pv +
                            " should have a colon after the macro"
                        )
                    else:
                        self.catch.append(
                            "FORMAT ERROR: " + r.pv +
                            " should not have a colon after the macro"
                        )

    def check_case(self, name):
        se = re.search('[a-z]', name)
        if se is not None:
            self.warnings.append(
                "CASING ERROR: " + name + " should be upper-case"
            )

    def check_chars(self, name):
        name = remove_macro(name)
        # Only contains a-z A-Z 0-9 _ :
        se = re.search(r'[^\w:]', name)
        if se is not None:
            self.catch.append(
                "CHARACTER ERROR: " + name + " contains illegal characters"
            )

    def check_candidates(self, group):
        if group.main == group.SP:
            self.sp_main_checks(group)
        elif group.main == group.SP_RBV:
            self.catch.append(
                "FORMAT ERROR: cannot have a SP:RBV "
                "on its own ({})".format(group.SP_RBV)
            )
        else:
            self.check_readback(group)

    def check_readback(self, group):
        # Is a standard readback
        if group.SP_RBV != "":
            if group.SP != "":
                # Both SP and SP:RBV Present, just check there formatting
                self.check_sp_formatting(":SP", group, group.SP)
                self.check_sp_formatting(":SP:RBV", group, group.SP_RBV)
            else:
                # has SP:RBV but no SP - wrong
                self.catch.append(
                    "PARAMETER ERROR: " + group.RB +
                    " has a :SP:RBV but not a :SP"
                )
        elif group.SP != "":
            # has SP but not SP:RBV
            self.catch.append(
                "PARAMETER ERROR: " + group.RB +
                " has a :SP but not a :SP:RBV"
            )
        # Has neither, read only
        return

    def sp_main_checks(self, group):
        # It is a SP, so it should have a readback alias (rule 6)
        combined_aliases = self.records_dict[group.main].aliases
        if group.SP_RBV is not None and group.SP_RBV in self.records_dict:
            combined_aliases += self.records_dict[group.SP_RBV].aliases
        if group.RB == '':
            self.catch.append(
                "FORMAT ERROR: " + group.SP +
                " does not have a correctly named readback alias"
            )
        elif group.RB not in combined_aliases:
            # SP is somehow main despite rb not being an alias?
            self.catch.append(
                "UNSPECIFIED ERROR: " + group.SP +
                " is not correct, please see the rules"
            )

    def check_sp_formatting(self, end, group, to_check):
        if not to_check.endswith(end):
            self.catch.append(
                "FORMAT ERROR: " + group.main +
                " does not have a correctly formatted " + end
            )
