import re
import argparse
import os
import glob
from db_parser import parse_db
from records import Record, Alias
from grouper import Grouper, RecordGroup

#Rules implemented:
# 1) Name should be uppercase
# 2) Colons are used as main separator
# 3) Names only use alphanumerics, underscore and colon
# 4) Adheres to :SP and SP:RBV format
# 5) If DUMMYPV and DUMMYPV:SP exists then DUMMYPV:SP:RBV should exist too (DUMMYPV:SP:RBV might be an alias).
# 6) If DUMMYPV:SP exists on its own that is okay - it is probably a push button who's status cannot be read, but it should have a SP:RBV alias for DUMMYPV
# 7) If DUMMYPV exists on its own it is okay (represents a read-only parameter)
# 8) Underscores:
#        a) Allowed if used for making a name clearer, e.g. X_POSITION
#        b) Not allowed to use the underscore instead of a ':', e.g. DUMMYPV_SP_RB

class DbChecker:
    def __init__(self, filename, debug=False):
        self.file = filename
        self.errors = []
        self.warnings = []
        self.debug = debug
        
    def check(self):
        print "\n** CHECKING", self.file, "**"
        records = parse_db(self.file)
        grouper = Grouper()
        
        groups = grouper.group_records(records)
        
        if self.debug:
            for s in groups.keys():
                print s, groups[s].RB, groups[s].SP, groups[s].SP_RBV
        
        for s in groups.keys():
            self.check_case(groups[s])
            self.check_chars(groups[s])
            self.check_candidates(groups[s], records)
                
        for w in self.warnings:
            print w
                    
        for e in self.errors:
            print e
                                
        print "** WARNING COUNT =", len(self.warnings), "**"
        print "** ERROR COUNT =", len(self.errors), "**"     
        
    def remove_macro(self, pvname):
        if pvname.find('$') != -1:
            left = pvname.rfind(')') + 1
            pvname = pvname[left:]
        return pvname

    def check_case(self, group):
        def check(name):
            se = re.search('[a-z]', name)
            if not se is None:
                self.errors.append("CASING ERROR: " + name + " should be upper-case")
        check(group.RB)
        check(group.SP)
        check(group.SP_RBV)
            
    def check_chars(self, group):
        def check(name):
            name = self.remove_macro(name)            
            #Only contains a-z A-Z 0-9 _ :
            se = re.search('[^\w_:]', name)
            if not se is None:
                self.errors.append("CHARACTER ERROR: " + name + " contains illegal characters")
        check(group.RB)
        check(group.SP)
        check(group.SP_RBV)
            
    def check_candidates(self, group, records):  
        ma1 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)$", group.main)
        ma2 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", group.main)
        #print group.main, group.RB, group.SP, group.SP_RBV
        if not ma1 is None:
            #It is a SP, so it should have a readback alias (rule 6)
            if group.RB == '':
                self.errors.append("FORMAT ERROR: " + group.SP + " does not have a correctly named readback alias")
            elif group.RB != '' and isinstance(records[group.RB], Alias):
                #This is okay
                return
            else:
                self.errors.append("UNSPECIFIED ERROR: " + group.SP + " is not correct, please see the rules")      
        elif not ma2 is None:
            self.errors.append("FORMAT ERROR: cannot have a SP:RBV on its own (%s)" % (group.SP) )
        else:
            #Is a standard readback
            if group.RB != '' and group.SP == '' and group.SP_RBV == '':
                #This is okay as it represents a read-only value (rule 7)
                return
            else:
                #Does it have SP:RBV but no SP - wrong
                if group.SP == "" and group.SP_RBV != '':
                    self.errors.append("PARAMETER ERROR: " + group.RB + " does not have a :SP")
                    return
                #If a group has a SP then it should have a SP:RBV (rule 5)
                if group.SP != "" and group.SP_RBV == "":
                    self.errors.append("PARAMETER ERROR: " + group.RB + " has a :SP but not a :SP:RBV")
                    
                #Finally check the format of the SP and SP:RBV (rule 4)
                if group.SP != "" and not group.SP.endswith(':SP'):
                    self.errors.append("FORMAT ERROR: " + group.RB + " does not have a correctly formatted :SP")
                if group.SP_RBV != "" and not group.SP_RBV.endswith(':SP:RBV'):
                    self.errors.append("FORMAT ERROR: " + group.RB + " does not have a correctly formatted :SP:RBV")
        
    def check_for_colons(self, names):
        #If there are no colons present then almost certainly the Db file is incorrect
        #In this case, do not bother checking any further
        for name in names: 
            if ':' in name:
                return True
        return False



        


    
    

        