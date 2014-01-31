import re
from records import Record, Alias
from grouper import Grouper


def parse_db(file):
    ''' '''
    #This regex matches the EPICS convention for PV names, e.g. a-z A-Z 0-9 _ - : [ ] < > ;
    #The ISIS convention uses a reduced set (a-z A-Z 0-9 _ :) but this is not relevant at this level
    regRecordStart = 'record\s*\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
    #Aliases look like alias("RECORDNAME","ALIASNAME")
    regAlias_alone = 'alias\s*\(\s*"([\w_\-\:\[\]<>;$\(\)]+)",\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
    
    f=open(file, 'r')
    
    records = {}
    inrecord = False
    record = None
    
    for line in f:
        maPV = re.match(regRecordStart, line)
        #maAlias1 = re.match(regAlias_inside, line)
        maAlias2 = re.match(regAlias_alone, line)
        
        if inrecord:
            #Look for end of record
            maEnd = re.match("}$", line.strip())
            if not (maEnd is None):
                inrecord = False
                records[record.name] = record
            else:
                #Look for alias
                regAlias_inside = 'alias\s*\(\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
                maAlias_inside = re.match(regAlias_inside, line)
                #Look for SIML
                regSiml = '\s+field\s*\(SIML,\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
                maSiml = re.match(regSiml, line)
                #Look for SDIS
                regSdis = '\s+field\s*\(SDIS,\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
                maSdis = re.match(regSdis, line)
                #Look for DTYP
                regDtyp = '\s+field\s*\(DTYP,\s*"([\w_\-\:\[\]<>;$\(\)\s]+)"\)'
                maDtyp = re.match(regDtyp, line)
                #Look for NELM
                regNelm = '\s+field\s*\(NELM,\s*"([\w_\-\:\[\]<>;$\(\)\s]+)"\)'
                maNelm = re.match(regNelm, line)
                #Look for FTVL
                regFtvl = '\s+field\s*\(FTVL,\s*"([\w_\-\:\[\]<>;$\(\)\s]+)"\)'
                maFtvl = re.match(regFtvl, line)
                
                if not (maAlias_inside is None):
                    #There is an alias
                    record.alias = Alias(maAlias_inside.groups()[0], record.type, record.name)
                if not (maSiml is None):
                    record.siml = maSiml.groups()[0]
                if not (maSdis is None):
                    record.sdis = maSdis.groups()[0]
                if not (maDtyp is None):
                    record.dtyp = maDtyp.groups()[0]
                if not (maNelm is None):
                    record.nelm = maNelm.groups()[0]
                if not (maFtvl is None):
                    record.ftvl = maFtvl.groups()[0]
        else:
            if not (maPV is None):
                #Found start of record
                #print "PV", maPV.groups()[1]
                inrecord = True
                record = Record(maPV.groups()[1], maPV.groups()[0])
            elif not (maAlias2 is None):
                #print "Alias", maAlias2.groups()[1]
                alias = Alias(maAlias2.groups()[1], parent = maAlias2.groups()[0])
                records[maAlias2.groups()[1]] = alias

    f.close()
    
    return records
    

