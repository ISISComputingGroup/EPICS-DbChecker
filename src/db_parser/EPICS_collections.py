"""
This file holds the classes to hold the record and field data
"""
import re


class Db:
    """
    This class holds all the data in a single db
    """
    def __init__(self, directory, records):
        self.directory = directory
        self.records = records

    def __len__(self):
        return len(self.records)

    def __str__(self):
        return str(self.directory)


class Record:
    """
    This class holds all the data about each record, including a list of
    fields within the record, and allows the constituent fields to be
    interrogated.
    """

    def __init__(self, rec_type, pv, infos, fields, aliases):
        self.type = rec_type
        self.pv = pv
        self.fields = fields
        self.infos = infos
        self.aliases = aliases
        # Test for whether the PV is a simulation
        if re.search(r'.SIM(:.|$)', pv) is not None:
            self.simulation = True
        else:
            self.simulation = False

        # Test for whether the PV is a disable
        if re.search(r'DISABLE', pv) is not None:
            self.disable = True
        else:
            self.disable = False

    def is_sim(self):
        return self.simulation

    def is_disable(self):
        return self.disable

    def __str__(self):
        return str(self.pv)

    def get_field_names(self):
        """
        This method returns all field names as a list
        """
        return [field.name for field in self.fields]

    def get_field_values(self):
        """
        This method returns all field values as a list
        """
        return [field.value for field in self.fields]

    def has_field(self, search):
        """
        This method checks all contained fields for instances of a
        pv given by the search input
        """
        for field in self.fields:
            if field.name == search:
                return True
        return False

    def get_field_value(self, search):
        """
        This method returns the values of the first field contained within
        the record that matches the search input
        If no field exists None is returned
        """
        for field in self.fields:
            if field.name == search:
                return field.value
        return None

    def get_field(self, search):
        """
        This method returns the values of the first field contained within
        the record that matches the search input
        If no field exists None is returned
        """
        for field in self.fields:
            if field.name == search:
                return field
        return None

    def get_type(self):
        """
        This method returns the PV type
        """
        return self.type

    def get_info(self, search):
        """
        This method returns a list of the values of all contained info
        fields that match the search input
        """
        found_values = []
        for info in self.infos:
            if info.name == search:
                found_values.append(info.value)
        return found_values

    def is_interest(self):
        """
        This method returns whether or not the record is of interest
        """
        for info in self.infos:
            if info.name == "INTEREST":
                return True
        return False

    def get_siml(self):
        for field in self.fields:
            if field.name == "SIML":
                return field.value
        return None

    def get_sdis(self):
        for field in self.fields:
            if field.name == "SDIS":
                return field.value
        return None

    def get_dtyp(self):
        for field in self.fields:
            if field.name == "DTYP":
                return field.value
        return None

    def get_nelm(self):
        for field in self.fields:
            if field.name == "NELM":
                return field.value
        return None

    def get_ftvl(self):
        for field in self.fields:
            if field.name == "FTVL":
                return field.value
        return None



class Field:
    """
    This class holds all the data about each field within a record,
    not using a dictionary as may not be unique
    """
    def __init__(self, name, value,has_macro=False):
        self.name = name.strip()
        self.value = value
        self.has_macro = has_macro

    def __str__(self):
        return str(self.name) + ":" + str(self.value)

    def unpack(self):
        return self.name, self.value
