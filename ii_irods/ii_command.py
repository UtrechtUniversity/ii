import argparse
import os.path
import sys
from ii_irods.coll_utils import collection_exists, verify_environment, get_cwd, set_cwd, get_home
from ii_irods.coll_utils import resolve_base_path
from ii_irods.session import setup_session
from ii_irods.utils import exit_with_error, print_error, print_debug


def entry():
    try:
        main()
    except KeyboardInterrupt:
        print("Script stopped by user.")


def main():
    args = parse_args()

    if args["command"] == "pwd":
        command_pwd(args)
    elif args["command"] == "cd":
        command_cd(args)
    else:
        exit_with_error("Error: unknown command")


def get_version():
    """Returns version number of script"""
    return "0.0.1 (prerelease prototype)"


def parse_args():
    """Returns command line arguments of the script.
       Exits with error message or help text when user provides
       wrong or no arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version',
                        version="iswitch version " + get_version())

    # Can't require a subparser because of need to maintain
    # backwards compatibility with Python 3.6
    subparsers = parser.add_subparsers(
        dest='command', help='command')

    pwd_parser = subparsers.add_parser("pwd",
                                       help='Print working directory/collection')
    pwd_parser.add_argument('--verbose', '-v', action='store_true', default=False,
                            help='Print verbose information for troubleshooting')

    cd_parser = subparsers.add_parser("cd",
                                      help='Change working directory/collection')
    cd_parser.add_argument('--verbose', '-v', action='store_true', default=False,
                           help='Print verbose information for troubleshooting')
    cd_parser.add_argument('directory', default=None, nargs='?',
                           help='Directory to change to')

    if len(sys.argv) == 1:
        parser.print_help()
        parser.exit()

    return vars(parser.parse_args())


def command_pwd(args):
    """Code for the pwd command"""
    _perform_environment_check(False)
    print(get_cwd(args["verbose"]))


def command_cd(args):
    """Code for the cd command"""
    _perform_environment_check()
    if args["directory"] is None:
        directory = get_home(args["verbose"])
        if args["verbose"]:
            print_debug("Defaulting cwd to home directory: " + directory)
    else:
        directory = args["directory"]

    if not directory.startswith("/"):
        directory = resolve_base_path(directory, get_cwd())
        if args["verbose"]:
            print_debug("Resolved relative directory to " + directory)

    session = setup_session()

    if not collection_exists(session, directory):
        exit_with_error("This collection does not exist.")

    try:
        set_cwd(directory, args["verbose"])
    except IOError:
        exit_with_error("IO error during reading or writing CWD data.")


def _perform_environment_check(check_auth=True):
    """Check if the environment configuration file is present, readable and
     has the required fields. By default, also check that a scrambled password
     file is present (unless check_auth is set to False). Prints any errors
     encountered and exits if there is a problem, otherwise returns."""
    correct, errors = verify_environment(check_auth)

    if not correct:
        print_error(
            "Cannot execute command because of problem(s) with environment:")
        for error in errors:
            print_error(" - " + error)
        sys.exit(1)
