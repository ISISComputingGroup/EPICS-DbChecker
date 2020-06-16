class Record:
    """Class for storing record details read from a Db file"""
    def __init__(self, name, type=None, alias=None):
        self.name = name
        self.type = type
        self.alias = alias
        self.siml = None
        self.sdis = None
        self.dtyp = None
        self.nelm = None  # waveform only
        self.ftvl = None  # waveform only


class Alias:
    """Class for storing alias details read from a Db file"""
    def __init__(self, name, type=None, parent=None):
        self.name = name
        self.type = type
        self.parent = parent
