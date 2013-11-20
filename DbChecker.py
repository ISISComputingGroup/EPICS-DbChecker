import re

#Rules implemented:
# 1) Name should be uppercase
# 2) Colons are used as main separator
# 3) Names only use alphanumerics, underscore and colon
# 4) Adheres to :SP and SP:RBV format
# 5) If DUMMYPV and DUMMYPV:SP exists then DUMMYPV:SP:RBV should exist too (DUMMYPV:SP:RBV might be an alias).
# 6) If DUMMYPV:SP exists on its own that is okay - it is probably a push button who's status cannot be read, but it should have an alias for DUMMYPV
# 7) If DUMMYPV exists on its own it is okay (represents a read-only parameter)

# NOTE: NOT CURRENTLY CHECKING FOR ALIASES - THIS WILL BE A MAJOR CHANGE!

#Underscores:
# a) Allowed if used for making a name clearer, e.g. X_POSITION
# b) Not allowed to use the underscore instead of a ':', e.g. DUMMYPV_SP_RB

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
        names, aliases = self.extract_names(self.file)
        records = self.gather_groups(names, aliases)
                    
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

    def extract_names(self, file):
        #This regex matches the EPICS convention for PV names, e.g. a-z A-Z 0-9 _ - : [ ] < > ;
        #This is not the same as the ISIS convention which is a-z A-Z 0-9 _ : this constraint will be checked later
        regPV = 'record\(\w+,\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
        
        #This regex looks for any aliases defined
        #The format is:
        # alias("firstAlias") inside a record
        # alias("canonicalName","secondAlias") if it is standalone
        regAlias_inside = 'alias\(\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
        regAlias_alone = 'alias\(\s*"([\w_\-\:\[\]<>;$\(\)]+)",\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'

        f=open(file, 'r')

        #Collect all the record names
        names = []
        aliases = []
        for line in f:
            #print line
            maPV = re.match(regPV, line)
            maAlias1 = re.match(regAlias_inside, line)
            maAlias2 = re.match(regAlias_alone, line)

            if not (maPV is None):
                pvname = maPV.groups()[0]
                #remove any macros
                if pvname.find('$') != -1:
                    left = pvname.rfind(')') + 1
                    pvname = pvname[left:]
                    names.append(pvname)
                    
            if not (maAlias1 is None):
                pvname = maAlias1.groups()[0]
                #remove any macros
                if pvname.find('$') != -1:
                    left = pvname.rfind(')') + 1
                    pvname = pvname[left:]
                    aliases.append(pvname)
            
            if not (maAlias2 is None):
                pvname = maAlias2.groups()[1]
                #remove any macros
                if pvname.find('$') != -1:
                    left = pvname.rfind(')') + 1
                    pvname = pvname[left:]
                    aliases.append(pvname)
                    
        return (names, aliases)
        
    def check_for_colons(self, names):
        #If there are no colons present then almost certainly the Db file is incorrect
        #In this case, do not bother checking any further
        for name in names: 
            if ':' in name:
                return True
        return False
            
    def gather_groups(self, names, aliases):
        #Gathering the groups together
        records = []
        stems = {}
        
        #Find potential stems
        for name in names:
            ma1 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
            ma2 = re.match("(.+)[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
            #ma3 = re.search("[_:](RBV|RB|READBACK|READ)$", name)
            if ma1 is None and ma2 is None:
                #Something like DUMMYPV would get here
                if not (name in stems.keys()):
                    stems[name] = ([], [])
                    continue
            else:
                #Something like DUMMYPV:SP or DUMMYPV:SP:RBV would get here
                if not (ma1 is None):
                    s = ma1.groups()[0]
                    if not (s in stems.keys()):
                        stems[s] = ([], [])
                        continue
                elif not (ma2 is None):
                    s = ma2.groups()[0]
                    if not (s in stems.keys()):
                        stems[s] = ([], [])
                        continue

        #Now find the related names
        for name in names:
            for s in stems.keys():
                ma1 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
                ma2 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
                ma3 = re.search(s + "[_:](RBV|RB|READBACK|READ)$", name)
                if ma1 != None or ma2 != None or ma3 != None:
                    stems[s][0].append(name)
                elif s == name:
                    #Also, add the readback (e.g. DUMMYPV) to the group if it exists
                    stems[s][0].append(name)
        
        #Check for related aliases
        for alias in aliases:
            for s in stems.keys():
                ma1 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", alias)
                ma2 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)$", alias)
                ma3 = re.search(s + "[_:](RBV|RB|READBACK|READ)$", alias)
                if ma1 != None or ma2 != None or ma3 != None or alias == s:
                    stems[s][1].append(alias)
        
        #Finally create the record objects
        for s in stems.keys():
            r = RecordGroup(s)
            r.candidates = stems[s][0]
            r.aliases = stems[s][1]
            records.append(r)

        if self.debug:
            print "GROUPS:"
            for s in stems.keys():
                print stems[s]
        return records    

if __name__ == '__main__':   
    #testfile = "./Examples/Agilent_33220A.db"   #Underscores used instead of colons
    #testfile = "./Examples/kepco.db"   #Incorrect SP:RBV
    #testfile = "./Examples/FL300.db"   #Has an SP but no SP:RBV
    #testfile = "./Examples/isisbeam.db"     #Is fine
    #testfile = "./Examples/examples.db"
    testfile = "./Examples/Stanford_PS350.db"
    
    checker = DbChecker(testfile)
    checker.check()


        


    
    

        