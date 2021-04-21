import re

from src.db_parser.lexer import Lexer
from src.db_parser.parser import Parser
from src.grouper import Grouper
from src.pv_checks import run_pv_checks


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


class DbChecker:
    def __init__(self, filename, debug=False):
        self.filename = filename
        self.file = open(filename)
        self.errors = []
        self.warnings = []
        self.debug = debug
        self.parsed_db = Parser(Lexer(self.file.read())).db()
        self.file.close()

    def pv_check(self):
        print("\n** CHECKING {}'s PVs **".format(self.filename))
        warnings, errors = run_pv_checks(self.parsed_db)
        print("**  PV ERROR COUNT = {} **".format(errors))
        print("**  PV WARNING COUNT = {} **".format(warnings))
        return warnings, errors

    def syntax_check(self):
        print("\n** CHECKING {}'s Syntax **".format(self.filename))
        grouper = Grouper()
        # Check for consistency in whether PV macros are followed by colons
        colon = None
        for r in self.parsed_db.records:
            if colon is None:
                n = self.remove_macro(r.pv, False)
                colon = n.startswith(':')
            else:
                n = self.remove_macro(r.pv, False)
                if n.startswith(':') != colon:
                    if colon:
                        self.errors.append(
                            "FORMAT ERROR: " + r.pv +
                            " should have a colon after the macro"
                        )
                    else:
                        self.errors.append(
                            "FORMAT ERROR: " + r.pv +
                            " should not have a colon after the macro"
                        )
        # Get list of all aliases and flatten it down.
        aliases = [alias for list in [record.aliases for record in self.parsed_db.records] for alias in list]
        record_names = [record.pv for record in self.parsed_db.records]
        records_dict = {name: record for name, record in zip(record_names, self.parsed_db.records)}
        groups = grouper.group_records(records_dict)
        if self.debug:
            for s in groups.keys():
                print(s, groups[s].RB, groups[s].SP, groups[s].SP_RBV)
        for s in groups.keys():
            self.check_case(groups[s])
            self.check_chars(groups[s])
            self.check_candidates(groups[s], aliases)

        for w in self.warnings:
            print(w)

        for e in self.errors:
            print(e)

        print("** WARNING COUNT = {} **".format(len(self.warnings)))
        print("** ERROR COUNT = {} **".format(len(self.errors)))

        return len(self.warnings), len(self.errors)

    def remove_macro(self, pvname, remove_colon=True):
        if pvname.find('$') != -1:
            left = pvname.rfind(')') + 1
            pvname = pvname[left:]
            # Remove leading : if there is one
            if remove_colon and pvname.startswith(':'):
                pvname = pvname[1:]
        return pvname

    def check_case(self, group):
        def check(name):
            se = re.search('[a-z]', name)
            if not se is None:
                self.errors.append(
                    "CASING ERROR: " + name + " should be upper-case"
                )

        check(group.RB)
        check(group.SP)
        check(group.SP_RBV)

    def check_chars(self, group):
        def check(name):
            name = self.remove_macro(name)
            # Only contains a-z A-Z 0-9 _ :
            se = re.search(r'[^\w_:]', name)
            if se is not None:
                self.errors.append(
                    "CHARACTER ERROR: " + name + " contains illegal characters"
                )

        check(group.RB)
        check(group.SP)
        check(group.SP_RBV)

    def check_candidates(self, group, aliases):
        ma1 = re.match(r"(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)$", group.main)
        ma2 = re.match(
            r"(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$",
            group.main
        )
        # print group.main, group.RB, group.SP, group.SP_RBV
        if ma1 is not None:
            # It is a SP, so it should have a readback alias (rule 6)
            if group.RB == '':
                self.errors.append(
                    "FORMAT ERROR: " + group.SP +
                    " does not have a correctly named readback alias"
                )
                print(group.SP)
            elif group.RB != '' and group.RB in aliases:
                # This is okay
                return
            else:
                self.errors.append(
                    "UNSPECIFIED ERROR: " + group.SP +
                    " is not correct, please see the rules"
                )
        elif ma2 is not None:
            self.errors.append(
                "FORMAT ERROR: cannot have a SP:RBV "
                "on its own ({})".format(group.SP)
            )
        else:
            # Is a standard readback
            if group.RB != '' and group.SP == '' and group.SP_RBV == '':
                # This is okay as it represents a read-only value (rule 7)
                return
            else:
                # Does it have SP:RBV but no SP - wrong
                if group.SP == "" and group.SP_RBV != '':
                    self.errors.append(
                        "PARAMETER ERROR: " + group.RB + " does not have a :SP"
                    )
                    return
                # If a group has a SP then it should have a SP:RBV (rule 5)
                if group.SP != "" and group.SP_RBV == "":
                    self.errors.append(
                        "PARAMETER ERROR: " + group.RB +
                        " has a :SP but not a :SP:RBV"
                    )

                # Finally check the format of the SP and SP:RBV (rule 4)
                if group.SP != "" and not group.SP.endswith(':SP'):
                    self.errors.append(
                        "FORMAT ERROR: " + group.RB +
                        " does not have a correctly formatted :SP"
                    )
                if group.SP_RBV != "" and not group.SP_RBV.endswith(':SP:RBV'):
                    self.errors.append(
                        "FORMAT ERROR: " + group.RB +
                        " does not have a correctly formatted :SP:RBV"
                    )
