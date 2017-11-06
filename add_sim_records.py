import re
import os
import argparse
from db_parser import parse_db, record_start_regex
from records import Record
from grouper import Grouper
from collections import Counter

# Only add SIM fields if type is one of the following:
ALLOWED_SIM_TYPES = ['ai', 'ao', 'bi', 'bo', 'mbbi', 'mbbo', 'stringin', 'stringout', 'longin', 'longout', 'waveform']


class NoMacroException(Exception):
    pass


def find_macro(name):
    """
    Splits a record name into the macro and the rest.
    :param name: The name of a record.
    :return: Tuple of (macro, pvname)
    """
    if name.find('$') != -1:
        left = name.rfind(')') + 1
        macro, pv = name[:left], name[left:]

        # Check for leading :
        # eg. PV name was something like $(P):TEMP rather than $(P)TEMP
        # This colon will count as part of the macro
        if pv.startswith(':'):
            return macro + ":", pv[1:]
        else:
            return macro, pv
    raise NoMacroException("PV {} contains no macros".format(name))


def get_sim_name(name):
    macro, pvname = find_macro(name)
    return macro + "SIM:" + pvname


def create_sim_record(old_record, new_name):
    rb_record = Record(new_name, old_record.type)
    rb_record.fields["SCAN"] = "Passive"
    rb_record.fields["DTYP"] = "Soft Channel"
    rb_record.nelm = old_record.nelm
    rb_record.ftvl = old_record.ftvl
    return rb_record


def generate_record_text(old_record, rb, sp, sp_rbv):
    out = ''
    if rb != '': 
        rb = get_sim_name(rb)

        out += str(create_sim_record(old_record, rb))

        if sp != '':
            sp = get_sim_name(sp)
            out += 'alias("{}","{}")\n\n'.format(rb, sp)
            
        if sp_rbv != '':
            sp_rbv = get_sim_name(sp_rbv)
            out += 'alias("{}","{}")\n\n'.format(rb, sp_rbv)
    elif sp != '':
        sp = get_sim_name(sp)

        out += str(create_sim_record(old_record, sp))
            
        if sp_rbv != '':
            sp_rbv = get_sim_name(sp_rbv)
            out += 'alias("{}","{}")\n\n'.format(sp, sp_rbv)
    elif sp_rbv != '':
        # Cannot think of any reason why a SP:RBV would exist on its own...
        sp_rbv = get_sim_name(sp_rbv)

        out += str(create_sim_record(old_record, sp_rbv))
        
    return out


def find_common_prefix(records):
    """
    Find the most common prefix in the records.
    This assumes that the prefix is a macro, which may or may not end with a colon.
    """
    prefixes = [find_macro(r)[0] for r in records.keys()]
    prefix_counter = Counter(prefixes)
    return prefix_counter.most_common(1)[0][0]


def generate_sim_records(records, sim_record_name, dis_record_name):
    sim_prefix = sim_record_name + ':'
    
    grouper = Grouper()
    groups = grouper.group_records(records)
    
    output = ""

    for g in groups.keys():
        sim_record_name = get_sim_name(groups[g].main)
        
        # Check sim record does not already exist - maybe someone started writing the records but got bored!
        if sim_record_name in records:
            continue
            
        # Skip record if it is a simulation record
        if groups[g].main.startswith(sim_prefix):
            continue
            
        # Skip adding sim record if the original is a soft record
        if records[groups[g].main].dtyp is None or records[groups[g].main].dtyp.lower() == "soft channel":
            continue

        # No point simulating SIM or DISABLE
        if groups[g].RB != sim_record_name and groups[g].RB != dis_record_name:
            typ = records[groups[g].main].type
            # Don't add simulation record unless the type is suitable
            if typ in ALLOWED_SIM_TYPES:            
                print("ADDED SIM RECORD: {}".format(sim_record_name))
                output += generate_record_text(records[groups[g].main], groups[g].RB, groups[g].SP, groups[g].SP_RBV)
                
    return output


def generate_modifed_db(file_in, file_out="generated.db", records={}, sim_record_name=None,
                        insert_sims=True, insert_disable=True):
    fin = open(file_in, 'r')
    fout = open(file_out, 'w')

    prefix = find_common_prefix(records)
    print("COMMON PREFIX: {}".format(prefix))

    if sim_record_name is None:
        sim_record_name = prefix + "SIM"
        print("Creating simulation PV: {}".format(sim_record_name))
        if insert_sims and sim_record_name not in records:
            sim_record = Record(sim_record_name, "bo")
            sim_record.fields["SCAN"] = "Passive"
            sim_record.fields["DTYP"] = "Soft Channel"
            sim_record.fields["ZNAM"] = "NO"
            sim_record.fields["ONAM"] = "YES"
            sim_record.fields["VAL"] = "$(RECSIM=0)"
            fout.write(str(sim_record))
    else:
        print("Using simulation PV: {}".format(sim_record_name))

    dis_record_name = prefix + "DISABLE"
    
    if insert_disable and dis_record_name not in records:
        dis_record = Record(dis_record_name, "bo")
        dis_record.fields["DESC"] = "Disable comms"
        dis_record.fields["PINI"] = "YES"
        dis_record.fields["VAL"] = "$(DISABLE=0)"
        dis_record.fields["OMSL"] = "supervisory"
        dis_record.fields["ZNAM"] = "COMMS ENABLED"
        dis_record.fields["ONAM"] = "COMMS DISABLED"
        fout.write(str(dis_record))

    curr_record = None
    for line in fin:
        matched_pv = re.match(record_start_regex, line)
        if matched_pv is not None:
            # Found start of record
            curr_record = records[matched_pv.groups()[1]]

        elif curr_record is not None:
            matched_end = re.match("}$", line.strip())

            if matched_end is not None:
                # Found end, insert sim and dis if necessary

                # Only add SIM and SDIS to allowed records which has a record type which is not soft channel
                if curr_record.type in ALLOWED_SIM_TYPES and curr_record.dtyp is not None and curr_record.dtyp.lower() != "soft channel":
                        if insert_sims and curr_record.siml is None:
                            name = get_sim_name(curr_record.name)                            
                            fout.write(Record.print_field("SIML", sim_record_name))
                            fout.write(Record.print_field("SIOL", name))
                        if insert_disable and curr_record.sdis is None:
                            fout.write(Record.print_field("DESC", dis_record_name))
        fout.write(line)
            
    fin.close()
    
    if insert_sims:
        new_records = generate_sim_records(records, sim_record_name, dis_record_name)
        
        # If no new records, don't write anything
        if new_records.strip() != "":
            fout.write("\n### SIMULATION RECORDS ###\n\n")
            fout.write(new_records)
    fout.close()
    
    
if __name__ == '__main__':   
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='The base file for adding records to')
    parser.add_argument('-o', '--output',  nargs='?', help='The name of the output file')
    parser.add_argument('-nd', '--no_disable', action='store_false',
                        help='Specify to not add a disable record to the new db')
    parser.add_argument('-s', '--sim_pv', nargs='?', type=str,
                        help='Specify the record to toggle simulation. If not specified one will be created.')
    args = parser.parse_args()

    if args.output is None:
        f = os.path.split(args.file)
        args.output = "sim_" + f[-1]

    db_records = parse_db(args.file)
    generate_modifed_db(args.file, args.output, db_records, insert_disable=args.no_disable, sim_record_name=args.sim_pv)
