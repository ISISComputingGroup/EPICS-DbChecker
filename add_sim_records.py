import re
import os
import argparse
from db_parser import parse_db
from records import Record, Alias
from grouper import Grouper, RecordGroup

#Only add SIM fields if type is one of the following:
ALLOWED_SIM_TYPES = ['ai', 'ao', 'bi', 'bo', 'mbbi', 'mbbo', 'stringin', 'stringout', 'longin', 'longout', 'waveform']

def find_macro(name):
    if name.find('$') != -1:
        left = name.rfind(')') + 1
        macro = name[:left]
        pvname = name[left:]
        return (macro, pvname)
    return None

def get_sim_name(name):
    ans = find_macro(name)
    
    if not ans is None:
        macro = ans[0]
        pvname = ans[1]
        #Check for leading :
        #eg. PV name was something like $(P):TEMP rather than $(P)TEMP
        if pvname.startswith(':'):
            pvname = pvname[1:]
            macro += ':'
        return macro + "SIM:" + pvname
    else:
        return "SIM:" + pvname
        
def add_waveform_specfic(nelm, ftvl):
    str = ''
    if not(nelm is None) or nelm == "":
        str += '    field(NELM, "' + nelm + '")' + '\n'
    if not(ftvl is None) or ftvl == "":
        str += '    field(FTVL, "' + ftvl + '")' + '\n'
    return str    

def generate_record_text(record, rb, sp, sp_rbv): 
    str = ''
    if rb != '': 
        rb = get_sim_name(rb)
            
        str += 'record(' + record.type + ', "' + rb + '")' + '\n'
        str += '{' + '\n'
        str += '    field(SCAN, "Passive")' + '\n'
        str += '    field(DTYP, "Soft Channel")' + '\n'
        str += add_waveform_specfic(record.nelm, record.ftvl)
        str += '}' + '\n' + '\n'
        
        if sp != '':
            sp = get_sim_name(sp)
            str += 'alias("'+ rb + '","' + sp + '")' + '\n' + '\n'
            
        if sp_rbv != '':
            sp_rbv = get_sim_name(sp_rbv)
            str += 'alias("'+ rb + '","' + sp_rbv + '")' + '\n' + '\n'
    elif sp != '':
        sp = get_sim_name(sp)
        str += 'record(' + record.type + ', "' + sp + '")' + '\n'
        str += '{' + '\n'
        str += '    field(SCAN, "Passive")' + '\n'
        str += '    field(DTYP, "Soft Channel")' + '\n'
        str += add_waveform_specfic(record.nelm, record.ftvl)
        str += '}' + '\n' + '\n'
            
        if sp_rbv != '':
            sp_rbv = get_sim_name(sp_rbv)
            str += 'alias("'+ sp + '","' + sp_rbv + '")' + '\n' + '\n'
    elif sp_rbv != '':
        #Cannot think of any reason why a SP:RBV would exist on its own...
        sp_rbv = get_sim_name(sp_rbv)
        str += 'record(' + record.type + ', "' + sp_rbv + '")' + '\n'
        str += '{' + '\n'
        str += '    field(SCAN, "Passive")' + '\n'
        str += '    field(DTYP, "Soft Channel")' + '\n'
        str += add_waveform_specfic(record.nelm, record.ftvl)
        str += '}' + '\n' + '\n'
        
    return str

def find_common_macro(records):
    #Find the most common macro name and whether it is followed by a colon
    macros = {}
    for r in records:
        m, pv = find_macro(records[r].name)
        if m in macros.keys():
            macros[m][0] += 1
        else:
            macros[m] = [0, pv.startswith(':')]
    best = None
    for m in macros.keys():
        if best is None or macros[m][0] > macros[best][0]:
            best = m
    return (best, macros[best][1])               

def generate_sim_records(records, sim_record_name, dis_record_name):      
    sim_prefix = sim_record_name + ':'
    
    grouper = Grouper()
    groups = grouper.group_records(records)
    
    output = ""

    for g in groups.keys():
        sim_record_name = get_sim_name(groups[g].main)
        
        #Check sim record does not already exist - maybe someone started writing the records but got bored!
        if sim_record_name in records:
            continue
            
        #Skip record if it is a simulation record 
        if groups[g].main.startswith(sim_prefix):
            continue
            
        #Skip adding sim record if the original is a soft record
        if records[groups[g].main].dtyp is None or records[groups[g].main].dtyp.lower() == "soft channel":
            continue

        #No point simulating SIM or DISABLE
        if groups[g].RB != sim_record_name and groups[g].RB != dis_record_name:
            typ = records[groups[g].main].type
            #Don't add simulation record unless the type is suitable
            if typ in ALLOWED_SIM_TYPES:            
                print "ADDED SIM RECORD =", sim_record_name
                output += generate_record_text(records[groups[g].main], groups[g].RB, groups[g].SP, groups[g].SP_RBV)
                
    return output

def generate_modifed_db(file_in, file_out="generated.db", records={}, sim_record_name=None,
                        insert_sims=True, insert_disable=True):
    regRecordStart = 'record\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'
    
    fin=open(file_in, 'r')
    fout=open(file_out, 'w')

    most, colon = find_common_macro(records)
    prefix = most
    if colon:
        prefix += ':'
    print "COMMON PREFIX =", prefix

    if sim_record_name is None:
        sim_record_name = prefix + "SIM"
        print("Creating simulation PV: {}".format(sim_record_name))
        if insert_sims and not sim_record_name in records:
            fout.write('record(bo, "' + sim_record_name + '")\n')
            fout.write('{\n')
            fout.write('    field(SCAN, "Passive")\n')
            fout.write('    field(DTYP, "Soft Channel")\n')
            fout.write('    field(ZNAM, "NO")\n')
            fout.write('    field(ONAM, "YES")\n')
            fout.write('    field(VAL, "$(RECSIM=0)")\n')
            fout.write('}\n\n')
    else:
        print("Using simulation PV: {}".format(sim_record_name))

    dis_record_name = prefix + "DISABLE"
    
    if insert_disable and not dis_record_name in records:
        fout.write('record(bo, "' + dis_record_name +'") \n')
        fout.write('{\n')
        fout.write('    field(DESC, "Disable comms")\n')
        fout.write('    field(PINI, "YES")\n')
        fout.write('    field(VAL, "$(DISABLE=0)")\n')
        fout.write('    field(OMSL, "supervisory")\n')
        fout.write('    field(ZNAM, "COMMS ENABLED")\n')
        fout.write('    field(ONAM, "COMMS DISABLED")\n')
        fout.write('}\n\n')

    curr_record = None
    for line in fin:
        maPV = re.match(regRecordStart, line)
        if maPV is not None:
            # Found start of record
            curr_record = records[maPV.groups()[1]]

        elif curr_record is not None:
            maEnd = re.match("}$", line.strip())

            if maEnd is not None:
                # Found end, insert sim and dis if necessary

                # Only add SIM and SDIS to allowed records which has a record type which is not soft channel
                if curr_record.type in ALLOWED_SIM_TYPES and curr_record.dtyp is not None and curr_record.dtyp.lower() != "soft channel":
                        if insert_sims and curr_record.siml is None:
                            name = get_sim_name(curr_record.name)                            
                            fout.write('    field(SIML, "' + sim_record_name +'")\n')
                            fout.write('    field(SIOL, "' + name+ '")\n')
                        if insert_disable and curr_record.sdis is None:
                            fout.write('    field(SDIS, "' + dis_record_name +'")\n')
        fout.write(line)
            
    fin.close()
    
    if insert_sims:
        new_records = generate_sim_records(records, sim_record_name, dis_record_name)
        
        #If no new records, don't write anything
        if new_records.strip() != "":
            fout.write("\n### SIMULATION RECORDS ###\n\n")
            fout.write(new_records)
    fout.close()
    
    
if __name__ == '__main__':   
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs=1, type=str, help='The base file for adding records to')
    parser.add_argument('-o', '--output',  nargs=1, default=[], help='The name of the output file')
    parser.add_argument('-nd', '--no_disable', action='store_false',
                        help='Specify to not add a disable record to the new db')
    parser.add_argument('-s', '--sim_pv', nargs='?', type=str,
                        help='Specify the record to toggle simulation. If not specified one will be created.')
    args = parser.parse_args()
    
    file = args.file[0]  
    
    if len(args.output) == 1:
        out = args.output[0]
    else:
        f = os.path.split(file)
        out = "sim_" + f[-1] 
    
    db_records = parse_db(file)
    generate_modifed_db(file, out, db_records, insert_disable=args.no_disable, sim_record_name=args.sim_pv)
