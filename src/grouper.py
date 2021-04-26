import re
from src.db_parser.parser import Parser
from src.db_parser.lexer import Lexer


class RecordGroup:
    def __init__(self, stem, main):
        self.stem = stem
        self.main = main  # The first non-alias PV found
        self.RB = ""
        self.SP = ""
        self.SP_RBV = ""

    def get_all(self):
        return [self.RB, self.SP, self.SP_RBV]


class Grouper:
    """A class for grouping related PVs together.
    A typical group would be PVNAME, PVNAME:SP, PVNAME:SP:RBV"""

    def __init__(self):
        self.record_groups = {}

    def group_records(self, record_dict, debug=False):
        # Get the record keys as a list because by
        # sorting it we can identify stems easily
        names = sorted(record_dict.keys())

        # Find potential stems
        for name in names:
            self.find_record_type(name)

        # Now find the related names
        for name in names:
            # get all aliases
            for alias in record_dict[name].aliases:
                ma1, ma2 = find_related_type(alias, name)
                # put alias in correct type, since its an alias for this record, must be at least one
                if ma1 is not None:
                    self.record_groups[name].SP = alias
                elif ma2 is not None:
                    self.record_groups[name].SP_RBV = alias
                else:
                    self.record_groups[name.split(":")[0]].RB = alias

            for s in self.record_groups.keys():
                # Don't read the first name
                if name == self.record_groups[s].main:
                    continue

                ma1, ma2 = find_related_type(name, s)

                # put record in matching type if it matches any
                if ma1 is not None:
                    self.record_groups[s].SP = name
                elif ma2 is not None:
                    self.record_groups[s].SP_RBV = name
                elif s == name:
                    self.record_groups[s].RB = name

        if debug:
            self.print_groups()
        return self.record_groups

    def find_record_type(self, name):
        # Stems are pure records, not aliases
        ma1 = re.match(
            r"(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name
        )
        ma2 = re.match(r"(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
        if ma1 is None and ma2 is None:
            # Something like DUMMYPV would get here
            if not (name in self.record_groups.keys()):
                self.record_groups[name] = RecordGroup(name, name)
                self.record_groups[name].RB = name
        else:
            # Something like DUMMYPV:SP or DUMMYPV:SP:RBV would get here
            if ma1 is not None:
                s = ma1.groups()[0]
                if not (s in self.record_groups.keys()):
                    self.record_groups[s] = RecordGroup(s, name)
                    self.record_groups[s].SP_RBV = name
            else:
                s = ma2.groups()[0]
                if not (s in self.record_groups.keys()):
                    self.record_groups[s] = RecordGroup(s, name)
                    self.record_groups[s].SP = name

    def print_groups(self):
        for s in self.record_groups.keys():
            print("s:{}, RB:{}, SP:{}, SP_RBV:{}".format(
                s, self.record_groups[s].RB, self.record_groups[s].SP,
                self.record_groups[s].SP_RBV)
            )


def find_related_type(search, name):
    ma1 = re.match("^" + re.escape(name) + r"[_:](SP|SETPOINT|SETP|SEP|SETPT)$", search)
    ma2 = re.match("^" + re.escape(name) + r"[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", search)
    return ma1, ma2


if __name__ == '__main__':
    # Simple test
    testfile = "./add_sim_records_tests/test_db.db"
    r = Parser(Lexer(testfile)).db()
    g = Grouper()
    g.group_records(r, True)
