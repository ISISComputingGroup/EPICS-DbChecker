import argparse
import glob
import os
import sys
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
    "DbChecker",  # tests that deliberately fail here
    "DbUnitChecker",  # tests that deliberately fail here
    "base",  # need to fix parsing of {} in fields before checking here
    "ICP_Binaries",  # contains files that end in .db not in .db format
    "cygwin",  # contains files that end in .db not in .db format
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
    "busy",
    "calc",
    "delaygen",  # Vendor DBs don't follow ISIS conventions
    "FileList",
    "FileServer",
    "googletest",
    "gateway",
    "sscan",
    "std",
    "StreamDevice",
    "timestampRecord",
    "pvxs",
    "motor",
    "motorExtensions",
    "devSnmp-nscl",  # Vendor DBs don't follow ISIS conventions
    "devPearl.db",  # Uses EPICS 7 JSON syntax which is not yet supported in the parser
    "gencontrol.db",  # Uses EPICS 7 JSON syntax which is not yet supported in the parser
    "runcontrol.db",  # Uses EPICS 7 JSON syntax which is not yet supported in the parser
    "settings_xml.db",  # Uses EPICS 7 JSON syntax which is not yet supported in the parser
    "testParseJSON.db",  # Uses EPICS 7 JSON syntax which is not yet supported in the parser
    "Lakeshore340.db",  # Uses EPICS 7 JSON syntax which is not yet supported in the parser
    "site-packages",  # Don't look inside site-packages dirs
]

# For the stricter checks, we only care about dbs written by ISIS
DIRECTORIES_TO_IGNORE_STRICT = [
    "DAQmxBase",
    "dbVerbose_20130124",
    "delaygen",
    "devIocStats",
    "dma4500m",
    "dna4500m",
    "ethercat",
    "galil",
    "iocbuilder-3-20",
    "ipApp",
    "knr1050",
    "lua",
    "MCAG_Base_Project",
    "NetShrVar",
    "NetStreams",
    "pixelman",
    "pr4000",
    "procServControl",
    "ReadASCII",
    "separator",
    "utilities",
    "utilitiesApp",
    "VisualDCT",
    "webget",
]
output_dir = ""


# return False if all OK, True on error
def check_files(db_files, strict, verbose, strict_error=False):
    failed_to_parse = []
    suite = unittest.TestSuite()
    for filename in db_files:
        try:
            filename = os.path.abspath(filename)
            with open(filename) as db_file:
                parsed_db = Parser(Lexer(db_file.read())).db()
            suite.addTest(
                DbCheckerTests(parsed_db, "test_pv_check", filename, verbose, strict_error)
            )
            if filename in strict:
                suite.addTest(
                    DbCheckerTests(parsed_db, "test_syntax_check", filename, verbose, strict_error)
                )
        except DbSyntaxError as e:
            print(f"Failed to parse {filename} because: {e}")
            failed_to_parse.append(filename)
        except UnicodeDecodeError as e:
            print("failed to open {}".format(filename))
            print(e)
        except IOError:
            print("FILE ERROR: File {} does not exist".format(filename))

    success = xmlrunner.XMLTestRunner(output=output_dir).run(suite).wasSuccessful()
    print(f"Test results output to {output_dir}")
    if len(failed_to_parse) > 0:
        print(f"Failed to parse the following files: \n{failed_to_parse}")
    return False if success and len(failed_to_parse) == 0 else True


def append_reduced_file_list(directory_to_walk, directory_to_ignore, list):
    for root, dirs, files in directory_to_walk:
        dirs[:] = [d for d in dirs if d not in directory_to_ignore]
        for file in files:
            if file.endswith(".db") and file not in directory_to_ignore:
                list.append(os.path.join(root, file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--directory", nargs=1, default=[], help="The directory to search for db files in"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=os.path.dirname(os.path.realpath(__file__)),
        help="The directory to output xml file to",
    )
    parser.add_argument("-f", "--files", nargs="*", default=[], help="The db file(s) to test")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Check all db files below the specified directory",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Run in verbose mode")
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        help="Run with strict checks as errors instead of warnings",
    )
    args = parser.parse_args()
    if len(args.directory) == 0 and len(args.files) == 0:
        parser.print_help()
    else:
        output_dir = args.output
        checks_failed = False
        if len(args.files) > 0:
            checks_failed = check_files(args.files, args.files, args.verbose, args.strict)
        if len(args.directory) > 0:
            if args.recursive:
                to_check = []
                strict_check = []
                dir_list = os.walk(args.directory[0])
                append_reduced_file_list(dir_list, DIRECTORIES_TO_ALWAYS_IGNORE, to_check)
                append_reduced_file_list(dir_list, DIRECTORIES_TO_IGNORE_STRICT, strict_check)

                checks_failed = check_files(to_check, strict_check, args.verbose, args.strict)
            else:
                # Find db files in directory
                os.chdir(args.directory[0])
                files = glob.glob("*.db")
                checks_failed = check_files(files, files, args.verbose, args.strict)
        sys.exit(1 if checks_failed else 0)
