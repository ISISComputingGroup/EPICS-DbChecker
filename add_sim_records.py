import re
import os
import argparse
from db_parser import parse_db
from records import Record, Alias
from grouper import Grouper, RecordGroup

#Only add SIM fields if type is one of the following:
ALLOWED_SIM_TYPES = ['ai', 'ao', 'bi', 'bo', 'mbbi', 'mbbo', 'stringin', 'stringout']

def generate_record_text(type, rb, sp, sp_rbv): 
    def insert_sim(name):
        if name.find('$') != -1:
            left = name.rfind(')') + 1
            macro = name[:left]
            pvname = name[left:]
            return macro + "SIM:" + pvname

    str = ''
    if rb != '': 
        rb = insert_sim(rb)
            
        str += 'record(' + type + ', "' + rb + '")' + '\n'
        str += '{' + '\n'
        str += '    field(SCAN, "Passive")' + '\n'
        str += '    field(DTYP, "Soft Channel")' + '\n'
        str += '}' + '\n' + '\n'
        
        if sp != '':
            sp = insert_sim(sp)
            str += 'alias("'+ rb + '","' + sp + '")' + '\n' + '\n'
            
        if sp_rbv != '':
            sp_rbv = insert_sim(sp_rbv)
            str += 'alias("'+ rb + '","' + sp_rbv + '")' + '\n' + '\n'
    elif sp != '':
        sp = insert_sim(sp)
        str += 'record(' + type + ', "' + sp + '")' + '\n'
        str += '{' + '\n'
        str += '    field(SCAN, "Passive")' + '\n'
        str += '    field(DTYP, "Soft Channel")' + '\n'
        str += '}' + '\n' + '\n'
            
        if sp_rbv != '':
            sp_rbv = insert_sim(sp_rbv)
            str += 'alias("'+ sp + '","' + sp_rbv + '")' + '\n' + '\n'
    elif sp_rbv != '':
        #Cannot think of any reason why a SP:RBV would exist on its own...
        sp_rbv = insert_sim(sp_rbv)
        str += 'record(' + type + ', "' + sp_rbv + '")' + '\n'
        str += '{' + '\n'
        str += '    field(SCAN, "Passive")' + '\n'
        str += '    field(DTYP, "Soft Channel")' + '\n'
        str += '}' + '\n' + '\n'
        
    return str
    
def generate_sim_records(db_read):
    records = parse_db(db_read)
    grouper = Grouper()
    groups = grouper.group_records(records)
    
    output = ""
    
    for g in groups.keys():
        #Check sim record does not already exist - maybe someone started writing the records but got bored!
        if '$(P)SIM:' + groups[g].main in records:
            continue
            
        #Skip record if it is a simulation record
        if groups[g].main.startswith("$(P)SIM"):
            continue

        #No point simulating SIM or DISABLE
        if groups[g].RB != "$(P)SIM" and groups[g].RB != "$(P)DISABLE":
            typ = records[groups[g].main].type
            #Don't add simulation record unless the type is suitable
            if typ in ALLOWED_SIM_TYPES:            
                output += generate_record_text(typ, groups[g].RB, groups[g].SP, groups[g].SP_RBV)
        
    return output

def generate_modifed_db(file_in, file_out="generated.db", records={}, insert_sims=True, insert_disable=True):
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
        fout.write('}\n\n')
    
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
                
                #Only add SIM and SDIS to allowed records
                if curr_record.type in ALLOWED_SIM_TYPES:
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
        new_records = generate_sim_records(file_in)
        
        #If no new records, don't write anything
        if new_records.strip() != "":
            fout.write("\n### SIMULATION RECORDS ###\n\n")
            fout.write(new_records)
    fout.close()
    
    
if __name__ == '__main__':   
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs=1, type=str, help='The base file for adding records to')
    parser.add_argument('-o', '--output',  nargs=1, default=[], help='The name of the output file')
    args = parser.parse_args()
    
    file = args.file[0]  
    
    if len(args.output) == 1:
        out = args.output[0]
    else:
        f = os.path.split(file)
        out = "sim_" + f[-1] 
    
    r = parse_db(file )
    generate_modifed_db(file, out, r)