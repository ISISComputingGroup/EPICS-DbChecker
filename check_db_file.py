import argparse
import os
import glob
from src.db_checker import DbChecker


def check_files(db_files, verbose):
    for f in db_files:
        try:
            fp = os.path.abspath(f)
            dbc = DbChecker(fp, verbose)
            dbc.check()
        except IOError:
            print("FILE ERROR: File {} does not exist".format(f))


if __name__ == '__main__':   
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory', nargs=1, default=[],
        help='The directory to search for db files in'
    )
    parser.add_argument(
        '-f', '--files',  nargs='*', default=[],
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
                tocheck = []
                for root, dirs, files in os.walk(args.directory[0]):
                    for file in files:
                        if file.endswith(".db"):
                            tocheck.append(os.path.join(root, file))
                check_files(tocheck, args.verbose)
            else:
                # Find db files in directory
                os.chdir(args.directory[0])
                files = glob.glob("*.db")
                check_files(files, args.verbose)
