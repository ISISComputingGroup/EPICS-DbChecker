import re
import os
import argparse
from src.grouper import Grouper
import textwrap
from src.db_parser.parser import Parser
from src.db_parser.lexer import Lexer

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
                original_record.get_nelm(), original_record.get_ftvl()
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


def find_common_macro(db):
    # Find the most common macro name and whether it is followed by a colon
    macros = {}
    for r in db.records:
        m, pv = find_macro(r.pv)
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
        if records[groups[g].main].get_dtyp() is None or \
                records[groups[g].main].get_dtyp().lower() == "soft channel":
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


def generate_modifed_db(file_in_path, db, file_out_path="generated.db", insert_sims=True, insert_disable=True):
    if db.records is None:
        db.records = []
    record_names = [record.pv for record in db.records]
    records_dict = {name: record for name, record in zip(record_names, db.records)}
    record_start_regex = r'record\((\w+),\s*"([\w_\-\:\[\]<>;$\(\)]+)"\)'

    with open(file_in_path, 'r') as in_file, \
            open(file_out_path, 'w') as out_file:
        prefix, colon = find_common_macro(db)
        if colon:
            prefix += ':'
        print("COMMON PREFIX = " + prefix)

        sim_record_name = prefix + "SIM"
        dis_record_name = prefix + "DISABLE"

        if insert_sims and sim_record_name not in records_dict:
            out_file.write('record(bo, "' + sim_record_name + '")\n')
            out_file.write('{\n')
            out_file.write('    field(SCAN, "Passive")\n')
            out_file.write('    field(DTYP, "Soft Channel")\n')
            out_file.write('    field(ZNAM, "NO")\n')
            out_file.write('    field(ONAM, "YES")\n')
            out_file.write('    field(VAL, "$(RECSIM=0)")\n')
            out_file.write('}\n\n')

        if insert_disable and dis_record_name not in records_dict:
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
                curr_record = records_dict[matched_pv.groups()[1]]

            elif curr_record is not None:
                if re.match("}$", line.strip()) is not None:
                    # Found end, insert sim and dis if necessary

                    # Only add SIM and SDIS to allowed records which has
                    # a record type which is not soft channel
                    if curr_record.type in ALLOWED_SIM_TYPES and \
                            curr_record.get_dtyp() is not None and \
                            curr_record.get_dtyp().lower() != "soft channel":
                        if insert_sims and curr_record.get_siml() is None:
                            name = get_sim_name(curr_record.pv)
                            out_file.write(
                                '    field(SIML, "' + sim_record_name + '")\n'
                            )
                            out_file.write('    field(SIOL, "' + name + '")\n')
                        if insert_disable and curr_record.get_sdis() is None:
                            out_file.write(
                                '    field(SDIS, "' + dis_record_name + '")\n'
                            )
            out_file.write(line)

        if insert_sims:
            new_records = generate_sim_records(
                records_dict, sim_record_name, dis_record_name
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
    
    filename = args.file[0]
    file = open(filename)
    if len(args.output) == 1:
        out = args.output[0]
    else:
        f = os.path.split(filename)
        out = "sim_" + f[-1] 
    
    db_records = Parser(Lexer(file.read())).db()
    file.close()
    generate_modifed_db(filename, db_records, out)
