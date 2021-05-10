import argparse
import os
import glob
import unittest
import xmlrunner
from src.db_checker import DbCheckerTests
from src.db_parser.common import DbSyntaxError
from src.db_parser.lexer import Lexer
from src.db_parser.parser import Parser

DIRECTORIES_TO_ALWAYS_IGNORE = [
    ".git",
    "O.Common",
    "O.windows-x64",
    "O.win32-x86",
    "bin",
    "lib",
    "include",
    ".project",
    ".ci",
    "areaDetector",  # Has some huge DBs which take forever to parse.
    ".vs",
    "DbChecker",  # tests that delibratly fail here
    "DbUnitChecker",  # tests that delibratly fail here
    "base",  # need to fix parsing of {} in fields before checking here
    "ICP_Binaries",  # contains files that end in .db not in .db format
    "seq",
    "caLab_1505",
    "EUROTHRM",
    "ether_ip",
    "optics",
    "fb_epid",
    # moved from ignore strict
    "nanodac",
    "asyn",
    "autosave",
    "axis",
    "axisRecord",
    "busy",
    "calc",
    "FileList",
    "FileServer",
    "googletest",
    "gateway",
    "sscan",
    "std",
    "StreamDevice",
    "timestampRecord",
    "motor",
    "motorExtensions"
]

# For the stricter checks, we only care about dbs written by locally
DIRECTORIES_TO_IGNORE_STRICT = [
    # "AG3631A",
    # "AG53220A", #Add to hardware list?
    # "Agilent_53220A", same as above
    # "aldn1000",
    # "ASTRIUM",
    #  "barndoors",
    #  "BKHOFF",

    #  "CAENMCA",
    #  "CAENVME",

    #  "CCD100",
    #  "CONEXAGP",
    #  "COUETTE",
    #  "cryosms",
    #  "CRYVALVE",
    #  "CYBAMAN",
    "DAQmxBase",
    "dbVerbose_20130124",
    #  "DELFTBPMAG",
    #  "DELFTDCMAG",
    #  "DELFTSHEAR",
    "devIocStats",
    #  "DFKPS",
    #  "dh2000",
    "dma4500m",
    "dna4500m",
    #  "ECLab",
    #  "EGXCOLIM",
    "ethercat",
    #  "FERMCHOP",

    #  "FINS",
    #  "flipprps",
    #  "FMR",
    #  "FZJDDFCH",
    #  "GALIL",
    "galil",
    #  "GAMRY",

    #  "GEMORC",

    #  "GP2Camera",
    #  "HAMEG8123",
    #  "Hameg_8123",
    #  "heliox",
    #  "HIFIMAG",
    #  "HIFIMAGS",
    #  "hlx503",
    # "HVCAEN",
    #  "HVCAENx527",
    #  "IEG",
    #  "ILM200",
    #  "indfurn",
    #  "INSTETC",
    #  "INSTRON",
    "iocbuilder-3-20",
    "ipApp",
    #  "IPS",
    #  "isisdae",
    #  "isisdaedata",
    #  "itc503",
    #  "jaws",
    #  "jsco4180",
    #  "JULABO",
    #  "keithley_2001",
    #  "kepco",
    #  "keylkg",
    #  "KHLY2700",
    "knr1050",
    #  "lakeshore340",
    #  "lakeshore372",
    #  "LINKAM95",
    #  "LINMOT",
    #  "LKSH336",
    #  "LKSH460",
    "lua",
    #  "magnet3D",
    #  "mca",
    "MCAG_Base_Project",
    #  "MCLEN",
    #  "mercuryitc",
    #  "mezflipr",
    #  "motionSetPoints",

    #  "moxa12XX",
    #  "MSH150",
    #  "MuonJaws",
    #  "NEOCERA",
    "NetShrVar",
    "NetStreams",
    #  "nGEM-BBTX",
    #  "ngpspsu",
    #  "NIMATRO",
    #  "NWPRTXPS",
    #  "oercone",
    #  "PIMOT",
    "pixelman",
    "pr4000",
    "procServControl",
    "ReadASCII",
    #  "RKNPS",
    #  "rotating_sample_changer",
    #  "RotBench",
    #  "RunControl",
    #  "RUNCTRL",
    #  "SAMPOS",
    "separator",
    #  "SKFChopper",
    #  "SKFMB350",
    #  "SM300",
    #  "SMC100",
    #  "sp2xx",
    #  "SPINFLIPPER306015",

    #  "superlogics",
    #  "TDK_LAMBDA_GENESYS",
    #  "TEKDMM40X0",
    #  "Tektronix_DMM_40X0",

    #  "TPG",
    #  "TRITON",
    #  "ttiEX355P",
    #  "ttiplp",
    #  "TWINCAT",
    "utilities",
    "utilitiesApp",
    "VisualDCT",
    #  "wbvalve",
    "webget",
    #  "WinDDE",
    #  "wm323",
    #  "zfcntrl"
]


def check_files(db_files, strict, verbose, strict_error=False):
    total_errors = 0
    total_strict_errors = 0
    total_warning = 0
    current_item = 1
    final_item = len(db_files)
    failed_to_parse = []
    failed = []
    suite = unittest.TestSuite()
    for f in db_files:
        try:
            fp = os.path.abspath(f)
            with open(fp) as file:
                parsed_db = Parser(Lexer(file.read())).db()
            suite.addTest(DbCheckerTests(parsed_db, "test_pv_check", f, verbose, strict_error))
            if f in strict:
                suite.addTest(DbCheckerTests(parsed_db, "test_syntax_check", f, verbose, strict_error))
            #dbc.parse_db_file()
            syntax_warnings = 0
            syntax_errors = 0
            # if f in strict:
            #     syntax_warnings, syntax_errors = dbc.test_syntax_check()
            # pv_warnings, pv_errors = dbc.test_pv_check()
            # if syntax_errors > 0 or pv_errors > 0:
            #     failed.append(f)
            # total_warning += syntax_warnings + pv_warnings
            # total_errors += syntax_errors + pv_errors
            # total_strict_errors += syntax_errors
        except DbSyntaxError as e:
            print(e)
            failed_to_parse.append(f)
        except IOError:
            print("FILE ERROR: File {} does not exist".format(f))

    success = xmlrunner.XMLTestRunner(output=os.path.dirname(os.path.realpath(__file__))).run(suite).wasSuccessful()
    if len(failed_to_parse) > 0:
        print("Failed to parse the following files: \n{}".format(failed_to_parse))
    if len(failed) > 0:
        print("The following files failed the checks: \n")
        for f in failed:
            print(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory', nargs=1, default=[],
        help='The directory to search for db files in'
    )
    parser.add_argument(
        '-f', '--files', nargs='*', default=[],
        help='The db file(s) to test')
    parser.add_argument(
        '-r', '--recursive', action='store_true',
        help='Check all db files below the specified directory'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Run in verbose mode'
    )
    parser.add_argument(
        '-s', '--strict', action='store_true', help='Run with strict checks as errors instead of warnings'
    )
    args = parser.parse_args()

    if len(args.directory) == 0 and len(args.files) == 0:
        parser.print_help()
    else:
        if len(args.files) > 0:
            check_files(args.files, args.files, args.verbose,args.strict)
        if len(args.directory) > 0:
            if args.recursive:
                to_check = []
                strict_check = []
                for root, dirs, files in os.walk(args.directory[0]):
                    dirs[:] = [d for d in dirs if d not in DIRECTORIES_TO_ALWAYS_IGNORE]
                    for file in files:
                        if file.endswith(".db"):
                            to_check.append(os.path.join(root, file))
                for root, dirs, files in os.walk(args.directory[0]):
                    dirs[:] = [d for d in dirs if d not in DIRECTORIES_TO_IGNORE_STRICT]
                    for file in files:
                        if file.endswith(".db"):
                            strict_check.append(os.path.join(root, file))
                check_files(to_check, strict_check, args.verbose, args.strict)
            else:
                # Find db files in directory
                os.chdir(args.directory[0])
                files = glob.glob("*.db")
                check_files(files, files, args.verbose,args.strict)
