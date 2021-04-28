import argparse
import os
import glob
from src.db_checker import DbChecker
from src.db_parser.common import DbSyntaxError
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
    "ICP_Binaries"  # contains files that end in .db not in .db format
]


def check_files(db_files, verbose):
    total_errors = 0
    total_warning = 0
    current_item = 1
    final_item = len(db_files)
    failed_to_parse = []
    failed = []
    for f in db_files:
        try:
            fp = os.path.abspath(f)
            dbc = DbChecker(fp, verbose)
            dbc.parse_db_file()
            syntax_warnings, syntax_errors = dbc.syntax_check()
            pv_warnings, pv_errors = dbc.pv_check()
            total_warning += syntax_warnings + pv_warnings
            total_errors += syntax_errors + pv_errors
        except DbSyntaxError as e:
            print(e)
            failed_to_parse.append(f)
        except IOError:
            print("FILE ERROR: File {} does not exist".format(f))
        finally:
            print("{} Files remaining".format(final_item - current_item))
            current_item += 1
    if final_item > 1:
        print("** TOTAL WARNING COUNT = {} **".format(total_warning))
        print("** TOTAL ERROR COUNT = {} **".format(total_errors))
    if len(failed_to_parse)>0:
        print("Failed to parse the following files: \n{}".format(failed_to_parse))


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
    args = parser.parse_args()

    if len(args.directory) == 0 and len(args.files) == 0:
        parser.print_help()
    else:
        if len(args.files) > 0:
            check_files(args.files, args.verbose)
        if len(args.directory) > 0:
            if args.recursive:
                to_check = []
                for root, dirs, files in os.walk(args.directory[0]):
                    dirs[:] = [d for d in dirs if d not in DIRECTORIES_TO_ALWAYS_IGNORE]
                    for file in files:
                        if file.endswith(".db"):
                            to_check.append(os.path.join(root, file))
                check_files(to_check, args.verbose)
            else:
                # Find db files in directory
                os.chdir(args.directory[0])
                files = glob.glob("*.db")
                check_files(files, args.verbose)
