import re
from records import Record, Alias
from grouper import Grouper

# This regex matches the EPICS convention for PV names, e.g. a-z A-Z 0-9 _ - : [ ] < > ;
# The ISIS convention uses a reduced set (a-z A-Z 0-9 _ :) but this is not relevant at this level
record_start_regex = 'record\s*\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'


def parse_db(file):
    # Aliases look like alias("RECORDNAME","ALIASNAME")
    alias_regex = 'alias\s*\(\s*"([\w_\-\:\[\]<>;$\(\)]+)",\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'

    field_regex = '\s+field\s*\(([A-Z]+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'

    with open(file, 'r') as f:

        records = {}
        inrecord = False
        record = None

        for line in f:
            if inrecord:
                # Look for end of record
                matched_end = re.match("}$", line.strip())
                if not (matched_end is None):
                    inrecord = False
                    records[record.name] = record
                else:
                    # Look for alias inside a record
                    inner_alias_regex = 'alias\s*\(\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
                    matched_inner_alias = re.match(inner_alias_regex, line)
                    # Look for a field
                    matched_field = re.match(field_regex, line)

                    if matched_inner_alias is not None:
                        # There is an alias
                        record.alias = Alias(matched_inner_alias.groups()[0], record.type, record.name)
                    if matched_field is not None:
                        if matched_field.groups()[0] == "SIML":
                            record.siml = matched_field.groups()[1]
                        if matched_field.groups()[0] == "SDIS":
                            record.sdis = matched_field.groups()[1]
                        if matched_field.groups()[0] == "DTYP":
                            record.dtyp = matched_field.groups()[1]
                        if matched_field.groups()[0] == "NELM":
                            record.nelm = matched_field.groups()[1]
                        if matched_field.groups()[0] == "FTVL":
                            record.ftvl = matched_field.groups()[1]
            else:
                matched_pv = re.match(record_start_regex, line)
                matched_alias = re.match(alias_regex, line)
                if matched_pv is not None:
                    # Found start of record
                    inrecord = True
                    record = Record(matched_pv.groups()[1], matched_pv.groups()[0])
                elif matched_alias is not None:
                    alias = Alias(matched_alias.groups()[1], parent=matched_alias.groups()[0])
                    records[matched_alias.groups()[1]] = alias
    
    return records
    

