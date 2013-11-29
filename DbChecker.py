import re

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

class RecordGroup:
    def __init__(self, stem):
        self.stem = stem
        self.candidates = []
        self.aliases = []
        self.RB = stem
        self.SP = ""
        self.SP_RBV = ""
        self.warnings = []
        self.errors = []
        self.type = ""
    
    def check_case(self):
        #Names should be upper-case
        def check(name):
            se = re.search('[a-z]', name)
            if not se is None:
                self.errors.append("CASING ERROR: " + name + " should be upper-case")
        check(self.stem)
        for n in self.candidates:
            check(n)
            
    def check_stem(self):
        ma1 = re.search("[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", self.stem)
        ma2 = re.search("[_:](SP|SETPOINT|SETP|SEP|SETPT)$", self.stem)
        ma3 = re.search("[_:](RBV|RB|READBACK|READ)$", self.stem)
        if ma1 != None or ma2 != None or ma3 != None:
            self.errors.append("FORMAT ERROR: " + self.stem + " is the incorrect format")
            
    def check_chars(self):
        def check(name):
            #Only contains a-z A-Z 0-9 _ :
            se = re.search('[^\w_:]', name)
            if not se is None:
                self.errors.append("CHARACTER ERROR: " + name + " contains illegal characters")
        check(self.stem)
        for n in self.candidates:
            check(n)
            
    def check_candidates(self):
        #If there is a DUMMYPV, DUMMYPV:SP and a DUMMYPV:SP:RBV then it is okay (rule 5)
        #If there is a DUMMYPV:SP but nothing else then it is okay providing there is an alias for DUMMYPV (rule 6)
        if len(self.candidates) > 3:
            self.warnings.append("WARNING: " + self.stem + " appears to have too many related records")       
        
        if len(self.candidates) == 1:
            #Could be a lone SP, which is fine if it has an alias for the stem (rule 6)
            if self.candidates[0] == self.stem + ':SP':
                if self.stem in self.aliases:
                    #It is okay
                    return
                else:
                    #Missing the stem
                    self.errors.append("FORMAT ERROR: " + self.candidates[0] + " does not have an alias called " + self.stem)
                    return
            #Or it could be a read-only value, so has no SP or SP:RBV which is okay
            if self.candidates[0] == self.stem:
                return
        
        #Check for :SP or :SP:RBV
        for name in self.candidates:
            if name == self.stem + ':SP':
                self.SP = name
            elif name == self.stem + ':SP:RBV':
                self.SP_RBV = name
        
        #Check the aliases
        for alias in self.aliases:
            if self.SP == "":
                if alias == self.stem + ':SP':
                    self.SP = alias
            if self.SP_RBV == "":
                if alias == self.stem + ':SP:RBV':
                    self.SP_RBV = alias
        
        if len(self.candidates) > 1 and self.SP == "":
            self.errors.append("FORMAT ERROR: " + self.stem + " does not have a correctly formatted :SP and/or :SP:RBV")
        #If a group has a SP then it should have a SP:RB
        if self.SP != "" and self.SP_RBV == "":
            self.errors.append("PARAMETER ERROR: " + self.stem + " has a :SP but not a :SP:RBV")
        
class DbChecker:
    def __init__(self, filename, debug=False):
        self.file = filename
        self.errorcount = 0
        self.warningcount = 0
        self.debug = debug
        
    def check(self):
        print "\n** CHECKING", self.file, "**"
        names = self.extract_names(self.file)
        records = self.gather_groups(names)
                    
        for r in records:
            r.check_case()
            r.check_chars()
            r.check_stem()
            r.check_candidates()
                
            for w in r.warnings:
                print w
                    
            for e in r.errors:
                print e
                
            self.errorcount += len(r.errors)
            self.warningcount += len(r.warnings)
                
        print "** WARNING COUNT =", self.warningcount, "**"
        print "** ERROR COUNT =", self.errorcount, "**"     

    def extract_names(self, file, remove_macro=True):
        #This regex matches the EPICS convention for PV names, e.g. a-z A-Z 0-9 _ - : [ ] < > ;
        #This is not the same as the ISIS convention which is a-z A-Z 0-9 _ : this constraint will be checked later
        regPV = 'record\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
        
        #This regex looks for any aliases defined
        #The format is:
        # alias("firstAlias") inside a record
        # alias("canonicalName","secondAlias") if it is standalone
        regAlias_inside = 'alias\(\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
        regAlias_alone = 'alias\(\s*"([\w_\-\:\[\]<>;$\(\)]+)",\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'

        f=open(file, 'r')

        #Collect all the record names
        records = {}
        for line in f:
            #print line
            maPV = re.match(regPV, line)
            maAlias1 = re.match(regAlias_inside, line)
            maAlias2 = re.match(regAlias_alone, line)
            
            if not (maPV is None):
                type = maPV.groups()[0]
                pvname = maPV.groups()[1]
                #remove any macros
                if remove_macro and pvname.find('$') != -1:
                    left = pvname.rfind(')') + 1
                    pvname = pvname[left:]
                records[pvname] = (pvname, type, None)
                    
            if not (maAlias1 is None):
                alias = maAlias1.groups()[0]
                #remove any macros
                if remove_macro and alias.find('$') != -1:
                    left = alias.rfind(')') + 1
                    alias = alias[left:]
                records[alias] = (alias, type, pvname)
            
            if not (maAlias2 is None):
                parent = maAlias2.groups()[0]
                alias = maAlias2.groups()[1]
                #remove any macros
                if remove_macro and alias.find('$') != -1:
                    left = alias.rfind(')') + 1
                    alias = alias[left:]
                if remove_macro and parent.find('$') != -1:
                    left = parent.rfind(')') + 1
                    parent = parent[left:]
                #Don't necessarily know the type at the moment
                records[alias] = (alias, None, pvname)
        
        #Find types for aliases when not found
        for a in records.keys():
            if records[a][1] is None and len(records[a]) ==3:
                parent = records[a][2]
                type = records[parent][1]
                records[a] = (a, type, parent)
                
        #Convert records to list
        reclist = []
        for key, value in records.iteritems():
            reclist.append(value)
                    
        return reclist
        
    def check_for_colons(self, names):
        #If there are no colons present then almost certainly the Db file is incorrect
        #In this case, do not bother checking any further
        for name in names: 
            if ':' in name:
                return True
        return False
            
    def gather_groups(self, names):
        #Gathering the groups together
        records = {}
        
        #Find potential stems
        for name, type, parent in names:
            if parent is None:
                ma1 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
                ma2 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
                #ma3 = re.search("[_:](RBV|RB|READBACK|READ)$", name)
                if ma1 is None and ma2 is None:
                    #Something like DUMMYPV would get here
                    if not (name in records.keys()):
                        records[name] = RecordGroup(name)
                        records[name].type = type
                        continue
                else:
                    #Something like DUMMYPV:SP or DUMMYPV:SP:RBV would get here
                    if not (ma1 is None):
                        s = ma1.groups()[0]
                        if not (s in records.keys()):
                            records[s] = RecordGroup(s)
                            records[s].type = type
                            continue
                    elif not (ma2 is None):
                        s = ma2.groups()[0]
                        if not (s in records.keys()):
                            records[s] = RecordGroup(s)
                            records[s].type = type
                            continue

        #Now find the related names
        for name, type, parent in names:
            for s in records.keys():
                ma1 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
                ma2 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
                ma3 = re.search(s + "[_:](RBV|RB|READBACK|READ)$", name)
                if ma1 != None or ma2 != None or ma3 != None:
                    if parent is None:
                        #Is a real PV
                       records[s].candidates.append(name)
                    else:
                        #Is an alias PV
                        records[s].aliases.append(name)
                elif s == name:
                    #Also, add the readback (e.g. DUMMYPV) to the group if it exists
                    records[s].candidates.append(name)
                    
        if self.debug:
            print "GROUPS:"
            for s in records.keys():
                print records[s]
        
        #Convert records to list
        reclist = []
        for key, value in records.iteritems():
            reclist.append(value)
        
        return reclist  

if __name__ == '__main__':   
    #testfile = "./Examples/Agilent_33220A.db"   #Underscores used instead of colons
    #testfile = "./Examples/kepco.db"   #Incorrect SP:RBV
    #testfile = "./Examples/FL300.db"   #Has an SP but no SP:RBV
    #testfile = "./Examples/isisbeam.db"     #Is fine
    #testfile = "./Examples/examples.db"
    testfile = "test_db.db"
    
    checker = DbChecker(testfile)
    checker.check()


        


    
    

        