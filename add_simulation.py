import re
from generate_sim_records import generate_sim_records
from db_parser import parse_db
from records import Record, Alias
from grouper import Grouper, RecordGroup

def modify_db(file_in, file_out="generated.db", records={}, insert_sims=True, insert_disable=True):
    regRecordStart = 'record\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
    
    fin=open(file_in, 'r')
    fout=open(file_out, 'w')
    
    inrecord = False
    curr_record = None
    
    if insert_sims and not "$(P)SIM" in records:
        fout.write('record(bo, "$(P)SIM")\n')
        fout.write('{\n')
        fout.write('    field(SCAN, "Passive")\n')
        fout.write('    field(DTYP, "Soft Channel")\n')
        fout.write('    field(ZNAM, "NO")\n')
        fout.write('    field(ONAM, "YES")\n')
        fout.write('}\n\n')
    
    if insert_disable and not "$(P)DISABLE" in records:
        fout.write('record(bo, "$(P)DISABLE") \n')
        fout.write('{\n')
        fout.write('    field(DESC, "Disable comms")\n')
        fout.write('    field(PINI, "YES")\n')
        fout.write('    field(VAL, "0")\n')
        fout.write('    field(OMSL, "supervisory")\n')
        fout.write('    field(ZNAM, "COMMS ENABLED")\n')
        fout.write('    field(ONAM, "COMMS DISABLED")\n')
        fout.write('}\n')
    
    for line in fin:
        maPV = re.match(regRecordStart, line)
        if not (maPV is None):
            #Found start of record
            inrecord = True
            curr_record = records[maPV.groups()[1]]
        else:
            maEnd = re.match("}$", line.strip())
            if not (maEnd is None):
                #Found end, insert sim and dis if necessary
                inrecord = False
                if not curr_record is None:
                    if insert_sims and curr_record.siml is None:
                        name = curr_record.name
                        if name.find('$') != -1:
                            left = name.rfind(')') + 1
                            name = name[left:]
                        fout.write('    field(SIML, "$(P)SIM")\n')
                        fout.write('    field(SIOL, "$(P)SIM:' + name+ '")\n')
                if not curr_record is None:
                    if insert_disable and curr_record.sdis is None:
                        fout.write('    field(SDIS, "$(P)DISABLE")\n')
        fout.write(line)
            
    fin.close()
    
    if insert_sims:
        fout.write("### SIMULATION RECORDS ###\n")
        fout.write(generate_sim_records(file_in))
    fout.close()
    
    
if __name__ == '__main__':   
    testfile = "./generate_sim_records_tests/test_db.db"
    r = parse_db(testfile)
    modify_db(testfile, "gen.db", r)