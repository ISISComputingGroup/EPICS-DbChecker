import re
from records import Record, Alias

class RecordGroup:
    def __init__(self, stem, main):
        self.stem = stem
        self.main = main #The first non-alias PV found
        self.RB = ""
        self.SP = ""
        self.SP_RBV = ""

class Grouper:
    '''A class for grouping related PVs together.
    A typical group would be PVNAME, PVNAME:SP, PVNAME:SP:RBV
    '''
    def __init__(self):
        pass
        
    def group_records(self, records, debug=False):
        #Get the record keys as a list because by sorting it we can identify stems easily 
        names = records.keys()
        names.sort()
        
        recordGroups = {}
        
        #Find potential stems
        for name in names:
            #Stems are pure records, not aliases
            if isinstance(records[name], Record):
                ma1 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
                ma2 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
                if ma1 is None and ma2 is None:
                    #Something like DUMMYPV would get here
                    if not (name in recordGroups.keys()):
                        recordGroups[name] = RecordGroup(name, name)
                        recordGroups[name].RB = name
                        continue
                else:
                    #Something like DUMMYPV:SP or DUMMYPV:SP:RBV would get here
                    if not (ma1 is None):
                        s = ma1.groups()[0]
                        if not (s in recordGroups.keys()):
                            recordGroups[s] = RecordGroup(s, name)
                            recordGroups[s].SP_RBV = name
                            continue
                    elif not (ma2 is None):
                        s = ma2.groups()[0]
                        if not (s in recordGroups.keys()):
                            recordGroups[s] = RecordGroup(s, name)
                            recordGroups[s].SP = name
                            continue         

        #Now find the related names
        for name in names:
            for s in recordGroups.keys():
                #Don't readd the first name
                if name == recordGroups[s].main:
                    continue
                
                ma1 = re.search("^" + re.escape(s) + "[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
                ma2 = re.search("^" + re.escape(s) + "[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
                
                if not ma1 is None:
                    recordGroups[s].SP = name
                elif not ma2 is None:
                    recordGroups[s].SP_RBV = name
                elif s == name:
                    recordGroups[s].RB = name
                #~ ma3 = re.search("^" + re.escape(s) + "[_:](RBV|RB|READBACK|READ)$", name)
                #~ if ma1 != None or ma2 != None or ma3 != None:
                       #~ recordGroups[s].append(name)
                #~ elif s == name:
                        #~ recordGroups[s].append(name)
                    
        if debug:
            print "GROUPS:"
            for s in recordGroups.keys():
                print s, recordGroups[s].RB, recordGroups[s].SP, recordGroups[s].SP_RBV
        
        return recordGroups
        
if __name__ == '__main__':  
    #Simple test
    from db_parser import parse_db
    testfile = "./generate_sim_records_tests/test_db.db"
    r = parse_db(testfile)
    g = Grouper()
    g.group_records(r, True)