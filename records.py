from collections import OrderedDict


class Record:
    """Class for storing record details read from a Db file"""
    def __init__(self, name, type=None, alias=None):
        self.name = name
        self.type = type
        self.alias = alias
        self.siml = None
        self.sdis = None
        self.dtyp = None
        self.nelm = None # waveform only
        self.ftvl = None # waveform only

        self.fields = OrderedDict()

    @staticmethod
    def print_field(field_name, field_val):
        """
        Helper method for creating a field string.
        """
        return '    field({}, "{}")\n'.format(field_name, field_val)

    def __str__(self):
        out = 'record({}, "{}")\n'.format(self.type, self.name)
        out += '{\n'
        for field, val in self.fields.items():
            if val is not None and not val == "":
                out += Record.print_field(field, val)
        if self.nelm is not None and not self.nelm == "":
            out += Record.print_field("NELM", self.nelm)
        if self.ftvl is not None and not self.ftvl == "":
            out += Record.print_field("FTVL", self.ftvl)
        out += '}\n\n'
        return out

class Alias:
    """Class for storing alias details read from a Db file"""
    def __init__(self, name, type=None, parent=None):
        self.name = name
        self.type = type
        self.parent = parent
