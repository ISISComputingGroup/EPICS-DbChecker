import re
from db_parser import parse_db
from records import Record, Alias
from grouper import Grouper
           
def generate_record_text(type, rb, sp, sp_rbv):
    str = ''
    if rb != '': #Seems unlikely!
        str += 'record(' + type + ', "$(P)SIM:' + rb + '")' + '\n'
        str += '{' + '\n'
        str += '    field(SCAN, "Passive")' + '\n'
        str += '    field(DTYP, "Soft Channel")' + '\n'
        str += '}' + '\n' + '\n'
    
    if sp != '':
        str += 'alias("$(P)SIM:'+ rb + '","$(P)SIM:' + sp + '")' + '\n' + '\n'
        
    if sp_rbv != '':
        str += 'alias("$(P)SIM:'+ rb + '","$(P)SIM:' + sp_rbv + '")' + '\n' + '\n'
    return str
    
def generate_sim_records_file(db_read, db_write):
    records = parse_db(db_read)
    grouper = Grouper()
    groups = grouper.group_records(records)
    
    f=open(db_write, 'w')
    
    for g in groups.keys():
        #No point simulating SIM or DISABLE
        if groups[g].RB != "SIM" and groups[g].RB != "DISABLE":
            typ = records[groups[g].main].type
            f.write(generate_record_text(typ, groups[g].RB, groups[g].SP, groups[g].SP_RBV))
        
    f.close()
    
def generate_sim_records(db_read):
    records = parse_db(db_read)
    grouper = Grouper()
    groups = grouper.group_records(records)
    
    output = ""
    
    for g in groups.keys():
        #No point simulating SIM or DISABLE
        if groups[g].RB != "SIM" and groups[g].RB != "DISABLE":
            typ = records[groups[g].main].type
            output += generate_record_text(typ, groups[g].RB, groups[g].SP, groups[g].SP_RBV)
        
    return output
                
if __name__ == '__main__': 
    generate_sim_records_file("./generate_sim_records_tests/test_db.db", 'sub_test_db.db')
    