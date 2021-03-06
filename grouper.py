import re
from records import Record


class RecordGroup:
    def __init__(self, stem, main):
        self.stem = stem
        self.main = main  # The first non-alias PV found
        self.RB = ""
        self.SP = ""
        self.SP_RBV = ""


class Grouper:
    """A class for grouping related PVs together.
    A typical group would be PVNAME, PVNAME:SP, PVNAME:SP:RBV"""

    def __init__(self):
        pass
        
    def group_records(self, records, debug=False):
        # Get the record keys as a list because by
        # sorting it we can identify stems easily
        names = sorted(records.keys())
        
        record_groups = {}
        
        # Find potential stems
        for name in names:
            # Stems are pure records, not aliases
            if isinstance(records[name], Record):
                ma1 = re.match(
                    r"(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name
                )
                ma2 = re.match(r"(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
                if ma1 is None and ma2 is None:
                    # Something like DUMMYPV would get here
                    if not (name in record_groups.keys()):
                        record_groups[name] = RecordGroup(name, name)
                        record_groups[name].RB = name
                        continue
                else:
                    # Something like DUMMYPV:SP or DUMMYPV:SP:RBV would get here
                    if not (ma1 is None):
                        s = ma1.groups()[0]
                        if not (s in record_groups.keys()):
                            record_groups[s] = RecordGroup(s, name)
                            record_groups[s].SP_RBV = name
                            continue
                    elif not (ma2 is None):
                        s = ma2.groups()[0]
                        if not (s in record_groups.keys()):
                            record_groups[s] = RecordGroup(s, name)
                            record_groups[s].SP = name
                            continue         

        # Now find the related names
        for name in names:
            for s in record_groups.keys():
                # Don't readd the first name
                if name == record_groups[s].main:
                    continue
                
                ma1 = re.search(
                    "^" + re.escape(s) + r"[_:](SP|SETPOINT|SETP|SEP|SETPT)$",
                    name
                )
                ma2 = re.search(
                    "^" + re.escape(s) + r"[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$",
                    name
                )
                
                if ma1 is not None:
                    record_groups[s].SP = name
                elif ma2 is not None:
                    record_groups[s].SP_RBV = name
                elif s == name:
                    record_groups[s].RB = name

        if debug:
            print("GROUPS:")
            for s in record_groups.keys():
                print(
                    s + record_groups[s].RB + record_groups[s].SP +
                    record_groups[s].SP_RBV
                )
        
        return record_groups


if __name__ == '__main__':  
    # Simple test
    from db_parser import parse_db
    testfile = "./add_sim_records_tests/test_db.db"
    r = parse_db(testfile)
    g = Grouper()
    g.group_records(r, True)
