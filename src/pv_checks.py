import re
import os
from collections import defaultdict

# list of those record types that should have a EGU field
EGU_list = {
    'ai', 'ao', 'calc', 'calcout', 'compress', 'dfanout', 'longin', 'longout',
    'mbbo', 'mbboDirect', 'permissive', 'sel', 'seq', 'state', 'stringin',
    'stringout', 'subArray', 'sub', 'waveform', 'archive', 'cpid', 'pid',
    'steppermotor'
}

EGU_sub_list = {'longin', 'longout', 'ai', 'ao'}

# list of records that should has an ASG defined
ASG_list = {'calc'}

# list of the accepted units. Standard prefixes to these units are also
# accepted and checked for below but we need to allow 'cm' explicitly as
# it is a non-standard unit prefix for metre
allowed_prefixable_units = {
    'A', 'angstrom', 'au', 'bar', 'B', 'bit', 'byte', 'C', 'count', 'degree',
    'eV', 'frame', 'g', 'G', 'hour', 'Hz', 'H', 'inch', 'interrupt', 'K', 'L',
    'm', 'min', 'minute', 'ohm', 'Oersted', '%', 'photon', 'pixel', 'radian',
    's', 'torr', 'step', 'T', 'V', 'Pa', 'deg', 'stp', 'W', 'N', 'F', 'event'
}

allowed_unit_prefixes = {'T', 'G', 'M', 'k', 'm', 'u', 'n', 'p', 'f'}

allowed_non_prefixable_units = {'cm', 'cdeg', 'rpm', 'rps', 'psig'}

allowed_standalone_units = {
    'cdeg/ss',  # Needed by the GORC. Latter is a special case because
    # cdeg/s^2 too long
    'uA hour',  # Needed by the ISISDAE
}


def process_units(processed_unit):
    # remove 1\ as this is ok as a unit as in 1\m but 1 on its own is not ok
    processed_unit = re.sub(r'1/', '', processed_unit).replace(" ", "")
    # split unit amalgamations and remove powers
    units_with_powers = re.split(r'[/ ()]', processed_unit)
    return units_with_powers


def expand_macro(raw_unit):
    # expand macro $(A) to a valid unit, expand $(A=B) to B
    processed_unit = re.sub(r'\$[({].*?=(.*)?[})]', r'\1', raw_unit)
    processed_unit = re.sub(r'\$[({].*?[})]', 'm', processed_unit)
    return processed_unit


def is_prefixed_unit(unit):
    """
    This method checks if a given unit has a prefix
    """
    unit_checklist = [len(unit) > len(base_unit) and
                      unit[-len(base_unit):] == base_unit and
                      unit[:-len(base_unit)] in allowed_unit_prefixes
                      for base_unit in allowed_prefixable_units]
    return any(unit_checklist)


def allowed_unit(raw_unit):
    """
    This method checks that the given unit conforms to standard
    """
    if raw_unit in allowed_standalone_units:
        return True

    processed_unit = expand_macro(raw_unit)
    units_with_powers = process_units(processed_unit)

    # allow power but not negative power so m^-1.
    # Reason is there is no latex so 1/m is much clearer here
    for u in units_with_powers:
        if '^' in u:
            base, expo = u.split('^')
            if expo[:1] == '-':
                return False
            else:
                units_with_powers = [base]

    units = filter(None, units_with_powers)
    return all(u in allowed_non_prefixable_units or
               u in allowed_prefixable_units or
               is_prefixed_unit(u) for u in units)


def build_failure_message(basemessage, submessages):
    """
    Builds a test failure message from a common descriptor and a list of
    individual failures.

    Args:
        basemessage: common base message
        submessages: list of submessages

    Returns:
        A formatted string containing the base and sub messages.
    """
    return "{}\n{}".format(basemessage, "\n".
                           join("   -> " + s for s in submessages))


def get_multiple_instances(db):
    """
    This method warns if there are multiple PVs with the same name in the
    project
    """
    failures = []
    dups = defaultdict(list)  # Makes a dict of lists
    for rec in db.records:
        dups[str(rec.pv)].append(rec)

    for k, v in dups.items():
        if len(v) > 1:
            failures.append("Multiple instances of {}".format(k))
    return failures


def get_multiple_properties_on_pvs(db):
    """
    This method checks that no PVs have duplicate fields
    """
    failures = []

    for rec in db.records:
        fields = rec.get_field_names()
        if len(set(fields)) != len(fields):
            dupes = set([i for i in fields if fields.count(i) > 1])
            failures.append("Multiple instances of fields {} on {}".
                            format(','.join(dupes), rec))
    return failures


def get_interest_units(db):
    """
    This method checks that interesting PVs have units
    """
    failures = []

    for rec in db.records:
        if rec.is_interest() and not rec.is_disable() and \
                (rec.get_type() in EGU_sub_list):
            unit = rec.get_field("EGU")
            if unit is None:
                failures.append("Missing units on {}".format(rec))
    return failures


def get_interest_calc_readonly(db):
    """
    This method checks that interesting PVs that are calc fields are set to
    readonly
    """
    failures = []

    for rec in db.records:
        if rec.is_interest() and (rec.get_type() in ASG_list):
            value = rec.get_field("ASG")
            if value != "READONLY":
                failures.append("Missing ASG on {}".format(rec))
    return failures


def get_desc_length(db):
    """
    This method checks that the description length on all PVs is no longer
    than 40 chars
    """
    failures = []

    for rec in db.records:
        desc = rec.get_field("DESC")
        if desc is not None:
            # remove macros
            desc = re.sub(r'\$\([^)]*\)', '', desc)
            if len(desc) > 40:
                failures.append("Description too long on {}".format(rec))
    return failures


def get_units_valid(db):
    """
    This method loops through all found records and finds the unique units.
    It then checks these units are standard
    """
    failures = []

    for rec in db.records:
        unit = rec.get_field("EGU")

        if unit is None or unit == "" or allowed_unit(unit):
            continue
        else:
            failures.append("Invalid unit '{}' on {}".format(unit, rec))

    return failures


def get_interest_descriptions(db):
    """
    This method checks all records marked as interesting for description fields
    """
    failures = []

    for rec in db.records:
        if rec.is_interest() and not rec.has_field("DESC"):
            failures.append("Missing description on {}".format(rec))
    return failures


def get_log_info_tags(db):
    """
    This method checks logging records to check that logging tags are not
    repeated and that the period is not defined in two ways.
    """
    failures = []

    # This originally was trying to check for duplicate logs etc. across multiple files simultaneously, but was failing
    # possible future change?

    log_fields = {}
    logging_period = None

    for rec in db.records:
        for info in rec.infos:
            info_name = info.name.lower().strip('"')
            if info_name.startswith("log"):
                previous_source = log_fields.get(info_name, None)
                if previous_source is not None:
                    failures.append(
                        "Invalid logging config: "
                        "{source} repeats the log info tag "
                        "{tag}".format(source=rec, tag=info_name)
                    )
                else:
                    log_fields[info_name] = (db, rec)

                if info_name == "log_period_seconds" or \
                        info_name == "log_period_pv":
                    if logging_period is None:
                        logging_period = (db, rec)
                    else:
                        failures.append(
                            "Invalid logging config: "
                            "{source} alters the logging period "
                            "type".format(source=rec, tag=info_name)
                        )

    return failures


# List of Errors to check for.
check_error = [get_interest_descriptions, get_units_valid, get_desc_length, get_interest_calc_readonly,
               get_interest_units, get_multiple_properties_on_pvs, get_log_info_tags, ]
# List of Warnings to check for.
check_warning = [get_multiple_instances]


def run_pv_checks(db):
    """
    This method runs through the checks and returns the total number of errors and warnings.
    """
    num_errors = 0
    num_warnings = 0
    for check in check_error:
        errors = check(db)
        num_errors += len(errors)
        if errors:
            print(build_failure_message("Error", errors))
    for check in check_warning:
        warnings = check(db)
        num_warnings += len(warnings)
        if warnings:
            print(build_failure_message("Warning", warnings))
    return num_warnings, num_errors
