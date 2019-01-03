"""
database parsing objects
"""
import re
from records import Record, Alias


def parse_db(filename):
    """
    Parse the db file for records
    Args:
        filename: file to parse

    Returns: dictionary of records with fields

    """

    # This regex matches the EPICS convention for PV names, e.g. a-z A-Z 0-9 _ - : [ ] < > ;
    # The ISIS convention uses a reduced set (a-z A-Z 0-9 _ :) but this is not relevant at this level
    reg_record_start = 'record\s*\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
    # Aliases look like alias("RECORDNAME","ALIASNAME")
    reg_alias_alone = 'alias\s*\(\s*"([\w_\-\:\[\]<>;$\(\)]+)",\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
    
    f = open(filename, 'r')
    
    records = {}
    inrecord = False
    record = None
    
    for line in f:
        pv_name_match = re.match(reg_record_start, line)
        alias_match = re.match(reg_alias_alone, line)
        
        if inrecord:
            record_end_match = re.match("}$", line.strip())
            if not (record_end_match is None):
                inrecord = False
                records[record.name] = record
            else:
                # Look for alias
                regex_alias_inside = 'alias\s*\(\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
                ma_alias_inside = re.match(regex_alias_inside, line)
                # Look for SIML
                reg_siml = '\s+field\s*\(SIML,\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
                ma_siml = re.match(reg_siml, line)
                # Look for SDIS
                reg_sdis = '\s+field\s*\(SDIS,\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
                ma_sdis = re.match(reg_sdis, line)
                # Look for DTYP
                reg_dtyp = '\s+field\s*\(DTYP,\s*"([\w_\-\:\[\]<>;$\(\)\s]+)"\)'
                ma_dtyp = re.match(reg_dtyp, line)
                # Look for NELM
                reg_nelm = '\s+field\s*\(NELM,\s*"([\w_\-\:\[\]<>;$\(\)\s]+)"\)'
                ma_nelm = re.match(reg_nelm, line)
                # Look for FTVL
                reg_ftvl = '\s+field\s*\(FTVL,\s*"([\w_\-\:\[\]<>;$\(\)\s]+)"\)'
                ma_ftvl = re.match(reg_ftvl, line)
                
                if not (ma_alias_inside is None):
                    # There is an alias
                    record.alias = Alias(ma_alias_inside.groups()[0], record.type, record.name)
                if not (ma_siml is None):
                    record.siml = ma_siml.groups()[0]
                if not (ma_sdis is None):
                    record.sdis = ma_sdis.groups()[0]
                if not (ma_dtyp is None):
                    record.dtyp = ma_dtyp.groups()[0]
                if not (ma_nelm is None):
                    record.nelm = ma_nelm.groups()[0]
                if not (ma_ftvl is None):
                    record.ftvl = ma_ftvl.groups()[0]
        else:
            if pv_name_match is not None:
                # Found start of record
                # print "PV", pv_name_match.groups()[1]
                record = Record(pv_name_match.groups()[1], pv_name_match.groups()[0])
                # check record doesn't start and stop on this line
                if re.match(".*{.*}", line) is None:
                    inrecord = True
                else:
                    records[record.name] = record

            elif not (alias_match is None):
                # print "Alias", alias_match.groups()[1]
                alias = Alias(alias_match.groups()[1], parent=alias_match.groups()[0])
                records[alias_match.groups()[1]] = alias

    f.close()
    
    return records
