import re
import os
import argparse
from db_parser import parse_db
from grouper import Grouper
import textwrap

# Only add SIM fields if type is one of the following:
ALLOWED_SIM_TYPES = [
    'ai', 'ao', 'bi', 'bo', 'mbbi', 'mbbo', 'stringin',
    'stringout', 'longin', 'longout', 'waveform'
]


def find_macro(name):
    if name.find('$') != -1:
        left = name.rfind(')') + 1
        macro = name[:left]
        pvname = name[left:]
        return macro, pvname
    return None


def get_sim_name(name):
    ans = find_macro(name)
    
    if ans is not None:
        macro = ans[0]
        pvname = ans[1]
        # Check for leading :
        # e.g. PV name was something like $(P):TEMP rather than $(P)TEMP
        if pvname.startswith(':'):
            pvname = pvname[1:]
            macro += ':'
        return macro + "SIM:" + pvname
    else:
        return "SIM:" + name


def add_waveform_specfic(nelm, ftvl):
    string = ''
    if not(nelm is None) or nelm == "":
        string += '    field(NELM, "' + nelm + '")\n'
    if not(ftvl is None) or ftvl == "":
        string += '    field(FTVL, "' + ftvl + '")\n'
    return string


def generate_single_record(original_record, name):
    return textwrap.dedent("""\
        record({},"{}")
        {{
            field(SCAN, "Passive")
            field(DTYP, "Soft Channel"){}
        }}
        
        """.format(
            original_record.type, name, add_waveform_specfic(
                original_record.nelm, original_record.ftvl
            )
        ))


def generate_record_text(record, rb, sp, sp_rbv): 
    string_builder = ''
    if rb != '': 
        rb = get_sim_name(rb)
        string_builder += generate_single_record(record, rb)
        
        if sp != '':
            sp = get_sim_name(sp)
            string_builder += 'alias("' + rb + '","' + sp + '")' + '\n\n'
            
        if sp_rbv != '':
            sp_rbv = get_sim_name(sp_rbv)
            string_builder += 'alias("' + rb + '","' + sp_rbv + '")' + '\n\n'
    elif sp != '':
        sp = get_sim_name(sp)
        string_builder += generate_single_record(record, sp)
            
        if sp_rbv != '':
            sp_rbv = get_sim_name(sp_rbv)
            string_builder += 'alias("' + sp + '","' + sp_rbv + '")' + '\n\n'
    elif sp_rbv != '':
        # Cannot think of any reason why a SP:RBV would exist on its own...
        sp_rbv = get_sim_name(sp_rbv)
        string_builder += generate_single_record(record, sp_rbv)
        
    return string_builder


def find_common_macro(records):
    # Find the most common macro name and whether it is followed by a colon
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
    return best, macros[best][1]


def generate_sim_records(records, sim_record_name, dis_record_name):
    sim_prefix = sim_record_name + ':'
    
    grouper = Grouper()
    groups = grouper.group_records(records)
    
    output = ""

    for g in groups.keys():
        sim_record_name = get_sim_name(groups[g].main)
        
        # Check sim record does not already exist - maybe someone
        # started writing the records but got bored!
        if sim_record_name in records:
            continue
            
        # Skip record if it is a simulation record
        if groups[g].main.startswith(sim_prefix):
            continue
            
        # Skip adding sim record if the original is a soft record
        if records[groups[g].main].dtyp is None or \
                records[groups[g].main].dtyp.lower() == "soft channel":
            continue

        # No point simulating SIM or DISABLE
        if groups[g].RB != sim_record_name and groups[g].RB != dis_record_name:
            typ = records[groups[g].main].type
            # Don't add simulation record unless the type is suitable
            if typ in ALLOWED_SIM_TYPES:            
                print("ADDED SIM RECORD = " + sim_record_name)
                output += generate_record_text(
                    records[groups[g].main], groups[g].RB,
                    groups[g].SP, groups[g].SP_RBV
                )
                
    return output


def generate_modifed_db(file_in_path, file_out_path="generated.db",
                        records=None, insert_sims=True, insert_disable=True):
    if records is None:
        records = {}
    record_start_regex = r'record\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'

    with open(file_in_path, 'r') as in_file, \
            open(file_out_path, 'w') as out_file:
        prefix, colon = find_common_macro(records)
        if colon:
            prefix += ':'
        print("COMMON PREFIX = " + prefix)

        sim_record_name = prefix + "SIM"
        dis_record_name = prefix + "DISABLE"

        if insert_sims and not sim_record_name in records:
            out_file.write('record(bo, "' + sim_record_name + '")\n')
            out_file.write('{\n')
            out_file.write('    field(SCAN, "Passive")\n')
            out_file.write('    field(DTYP, "Soft Channel")\n')
            out_file.write('    field(ZNAM, "NO")\n')
            out_file.write('    field(ONAM, "YES")\n')
            out_file.write('    field(VAL, "$(RECSIM=0)")\n')
            out_file.write('}\n\n')

        if insert_disable and not dis_record_name in records:
            out_file.write('record(bo, "' + dis_record_name + '") \n')
            out_file.write('{\n')
            out_file.write('    field(DESC, "Disable comms")\n')
            out_file.write('    field(PINI, "YES")\n')
            out_file.write('    field(VAL, "$(DISABLE=0)")\n')
            out_file.write('    field(OMSL, "supervisory")\n')
            out_file.write('    field(ZNAM, "COMMS ENABLED")\n')
            out_file.write('    field(ONAM, "COMMS DISABLED")\n')
            out_file.write('}\n\n')

        curr_record = None
        for line in in_file:
            matched_pv = re.match(record_start_regex, line)
            if matched_pv is not None:
                # Found start of record
                curr_record = records[matched_pv.groups()[1]]

            elif curr_record is not None:
                if re.match("}$", line.strip()) is not None:
                    # Found end, insert sim and dis if necessary

                    # Only add SIM and SDIS to allowed records which has
                    # a record type which is not soft channel
                    if curr_record.type in ALLOWED_SIM_TYPES and \
                            curr_record.dtyp is not None and \
                            curr_record.dtyp.lower() != "soft channel":
                        if insert_sims and curr_record.siml is None:
                            name = get_sim_name(curr_record.name)
                            out_file.write(
                                '    field(SIML, "' + sim_record_name + '")\n'
                            )
                            out_file.write('    field(SIOL, "' + name + '")\n')
                        if insert_disable and curr_record.sdis is None:
                            out_file.write(
                                '    field(SDIS, "' + dis_record_name + '")\n'
                            )
            out_file.write(line)

        if insert_sims:
            new_records = generate_sim_records(
                records, sim_record_name, dis_record_name
            )

            # If no new records, don't write anything
            if new_records.strip() != "":
                out_file.write("\n### SIMULATION RECORDS ###\n\n")
                out_file.write(new_records)


if __name__ == '__main__':   
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file', nargs=1, type=str, help='The base file for adding records to'
    )
    parser.add_argument(
        '-o', '--output',  nargs=1, default=[],
        help='The name of the output file'
    )
    args = parser.parse_args()
    
    file = args.file[0]  
    
    if len(args.output) == 1:
        out = args.output[0]
    else:
        f = os.path.split(file)
        out = "sim_" + f[-1] 
    
    db_records = parse_db(file)
    generate_modifed_db(file, out, db_records)
