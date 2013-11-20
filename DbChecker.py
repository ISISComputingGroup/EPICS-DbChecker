import re

#Rules implemented:
# 1) Name should be uppercase
# 2) Colons are used as main separator
# 3) Names only use alphanumerics, underscore and colon
# 4) Adheres to :SP and SP:RBV format
# 5) If :SP exists then :SP:RBV should exist too

#Underscores:
# a) Allowed if used for making a name clearer, e.g. X_POSITION
# b) Not allowed to use the underscore instead of a ':', e.g. TEMP_SP_RB

class RecordGroup:
    def __init__(self, stem):
        self.stem = stem
        self.candidates = []
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
        if len(self.candidates) > 2:
            self.warnings.append("WARNING: " + self.stem + " appears to have too many related records")       
        #Check for :SP or :SP:RBV
        for name in self.candidates:
            if name == self.stem + ':SP':
                self.SP = name
            elif name == self.stem + ':SP:RBV':
                self.SP_RBV = name
        
        if len(self.candidates) > 0 and self.SP == "":
            self.errors.append("FORMAT ERROR: " + self.stem + " does not have a correctly formatted :SP and/or :SP:RBV")
        #If a group has a SP then it should have a SP:RB
        if self.SP != "" and self.SP_RBV == "":
            self.errors.append("PARAMETER ERROR: " + self.stem + " has a :SP but not a :SP:RBV")
        
class DbChecker:
    def __init__(self, filename):
        self.file = filename
        self.errorcount = 0
        self.warningcount = 0
        
    def check(self):
        print "\n** CHECKING", self.file, "**"
        names = self.extract_names(self.file)
        #print names
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

    def extract_names(self, file):
        #This regex matches the EPICS convention for PV names, e.g. a-z A-Z 0-9 _ - : [ ] < > ;
        #This is not the same as the ISIS convention which is a-z A-Z 0-9 _ :
        regex = 'record\(\w+,\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'

        f=open(file, 'r')

        #Collect all the record names
        names = []
        for line in f:
            #print line
            ma = re.match(regex, line)

            if not ma is None:
                pvname = ma.groups()[0]
                #print pvname
                #remove any macros
                if pvname.find('$') != -1:
                    left = pvname.rfind(')') + 1
                    pvname = pvname[left:]
                    names.append(pvname)

        return names
        
    def check_for_colons(self, names):
        #If there are no colons present then almost certainly the Db file is incorrect
        #In this case, do not bother checking any further
        for name in names: 
            if ':' in name:
                return True
        return False
            
    def gather_groups(self, names):
        #Gathering the groups together
        records = []
        stems = {}
        
        #Find potential stems
        for name in names:
            ma1 = re.search("[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
            ma2 = re.search("[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
            #ma3 = re.search("[_:](RBV|RB|READBACK|READ)$", name)
            if ma1 == None and ma2 == None:
                #Probably a new stem
                stems[name] = []
        #Now find the related names
        #print stems
        for name in names:
            for s in stems.keys():
                ma1 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)[_:](RBV|RB|READBACK|READ)$", name)
                ma2 = re.search(s + "[_:](SP|SETPOINT|SETP|SEP|SETPT)$", name)
                ma3 = re.search(s + "[_:](RBV|RB|READBACK|READ)$", name)
                if ma1 != None or ma2 != None or ma3 != None:
                    stems[s].append(name)
        #Finally create the record objects
        #print stems
        for s in stems.keys():
            r = RecordGroup(s)
            r.candidates = stems[s]
            records.append(r)       
    
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


        


    
    

        