import argparse
from fnmatch import fnmatch
import os.path
import sys

from ii_irods.coll_utils import collection_exists, verify_environment, get_cwd, set_cwd, get_home
from ii_irods.coll_utils import resolve_base_path, convert_to_absolute_path, get_dataobjects_in_collection
from ii_irods.coll_utils import get_direct_subcollections, get_subcollections
from ii_irods.do_utils import get_dataobject_info, dataobject_exists
from ii_irods.ls_formatters import TextListFormatter, CSVListFormatter
from ii_irods.ls_formatters import JSONListFormatter, YAMLListFormatter
from ii_irods.session import setup_session
from ii_irods.utils import exit_with_error, print_error, print_debug, debug_dumpdata


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
    elif args["command"] == "ls":
        command_ls(args)
    elif args["command"] == "find":
        command_find(args)
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

    ls_parser = subparsers.add_parser("ls",
                                      help='List collections or data objects')
    ls_parser.add_argument('--verbose', '-v', action='store_true', default=False,
                           help='Print verbose information for troubleshooting')
    ls_parser.add_argument('queries', default=None, nargs='*',
                           help='Collection, data object or data object wildcard')
    ls_parser.add_argument("-m", "--format", dest='format', default='plain',
                           help="Output format", choices=['plain', 'json', 'csv', "yaml"])
    ls_parser.add_argument("-s", "--sort", dest="sort", default='name',
                           help="Propery to use for sorting", choices=['name', 'ext', 'size', 'date', "unsorted"])
    ls_parser.add_argument("-H", "--hr-size", default='default', dest="hrsize",
                           help="Whether to print human-readable sizes [yes,no,default]." +
                           "By default, enable human-readable for text output, disable for other formats.",
                           choices=['default', 'yes', 'no'])
    ls_parser.add_argument('--recursive', '-r', action='store_true', default=False,
                           help='Include contents of subcollections')
    ls_parser.add_argument('-l', action='store_true', default=False,
                           help='Display replicas with size, resource, owner, date')
    ls_parser.add_argument('-L', action='store_true', default=False,
                           help='like -l, but also display checksum and physical path')

    find_parser = subparsers.add_parser("find",
                                      help='Find data objects by property')
    find_parser.add_argument('--verbose', '-v', action='store_true', default=False,
                           help='Print verbose information for troubleshooting')
    find_parser.add_argument('queries', default=None, nargs='*',
                           help='Collection, data object or data object wildcard')
    find_parser.add_argument('--print0', '-0', action='store_true', default=False,
                           help='Use 0 byte delimiters between results')

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


def command_ls(args):
    """Code for the ls command"""
    _perform_environment_check()

    if args["l"] and args["L"]:
        exit_with_error(
            "The -l and -L switches of the ls command are incompatible.")

    session = setup_session()
    expanded_queries = _expand_query_list(session, args["queries"],
        args["recursive"], args["verbose"])
    query_results = retrieve_object_info(session, expanded_queries, args["sort"])
    if args["l"] or args["L"]:
        _ls_print_results(query_results, args)
    else:
        dedup_results = _replica_results_dedup(query_results)
        _ls_print_results(dedup_results, args)


def command_find(args):
    """Code for the find command"""
    _perform_environment_check()

    session = setup_session()
    expanded_queries = _expand_query_list(session, args["queries"], True, args["verbose"])
    query_results = retrieve_object_info(session, expanded_queries, "unsorted")

    # Filters go here

    dedup_results = _replica_results_dedup(query_results)
    _find_print_results(dedup_results, args["print0"])

def _expand_query_list(session, queries, recursive=False, verbose=False):
    """This function expands ls queries by resolving relative paths,
    expanding wildcards and expanding recursive queries. If the user provides no
    queries, the method defaults to a single nonrecursive query for the current working directory."""
    results = []

    # If no queries are supplied by the user, default to a query for the
    # current working directory
    if len(queries) == 0:
        queries = [get_cwd()]

    # Wildcard expansion is performed first, so it can be combined with other types
    # of expansion, such as recursive expansion of subcollections later. Each collection
    # or data object is expanded only once.
    preprocessed_queries = []
    already_expanded = {}
    for query in queries:
        # Currently only wildcards without a collection path are supported
        # e.g. "*.dat", but not "../*.dat" or "*/data.dat".
        if "/" not in query and ( "?" in query or "*" in query):
            for d in get_dataobjects_in_collection(session, get_cwd()):
                if fnmatch(d["name"],query) and d["full_name"] not in already_expanded:
                    preprocessed_queries.append(d["full_name"])
                    already_expanded[d["full_name"]] = 1
            for c in get_direct_subcollections(session,get_cwd()):
                parent, coll = os.path.split(c["name"])
                if fnmatch(coll, query) and d["name"] not in already_expanded:
                    preprocessed_queries.append(c["name"])
                    already_expanded[d["name"]] = 1
        else:
            preprocessed_queries.append(query)

    for query in preprocessed_queries:
        absquery = convert_to_absolute_path(query)
        if collection_exists(session, absquery):
            results.append({"original_query": query, "expanded_query": absquery,
                            "expanded_query_type": "collection"})
            if verbose:
                print_debug("Argument \"{}\" is a collection.".format(query))
            if recursive:
                for subcollection in get_subcollections(session, absquery):
                    if verbose:
                        print_debug("Recursively adding subcollection " +
                            subcollection + " to queries.")
                    results.append ( {"original_query": query,
                        "expanded_query": subcollection,
                        "expanded_query_type": "collection" } )
        elif dataobject_exists(session, absquery):
            results.append({"original_query": query, "expanded_query": absquery,
                            "expanded_query_type": "dataobject"})
            if verbose:
                print_debug("Argument \"{}\" is a data object.".format(query))
        else:
            print_error(
                "Query \"{}\" could not be resolved. Ignoring ... ".format(query))

    return results


def _replica_results_dedup(queries):
    """This method deduplicates data object results within a query, so that ls displays data objects
    one time, instead of once for every replica."""
    deduplicated_queries = []
    for query in queries:
        new_query = query.copy()

        if "results" in query:
            objects_seen = {}
            dedup_results = []
            results = query["results"]

            for result in results:
                if result["type"] == "dataobject":
                    full_name = result["full_name"]
                    if full_name not in objects_seen:
                        objects_seen[full_name] = 1
                        dedup_results.append(result)
                else:
                    dedup_results.append(result)

            new_query["results"] = dedup_results

        deduplicated_queries.append(new_query)

    return deduplicated_queries


def _ls_print_results(results, args):

    if args["format"] == "plain":
        formatter = TextListFormatter()
    elif args["format"] == "json":
        formatter = JSONListFormatter()
    elif args["format"] == "yaml":
        formatter = YAMLListFormatter()
    elif args["format"] == "csv":
        formatter = CSVListFormatter()
    else:
        print("Output format {} is not supported.".format(args["format"]))

    formatter.print_data(results, args)

def _find_print_results(data, print0):

    def _find_print(m):
        if print0:
            print(m, end="\0")
        else:
            print(m)

    for query in data:
        querytype = query["expanded_query_type"]
        if querytype == "collection" and "results" in query:
            results = query["results"]
            for result in results:
                if result["type"] == "dataobject":
                    _find_print(result["full_name"])
        elif querytype == "dataobject" and "expanded_query" in query:
            _find_print(query["expanded_query"])
        else:
            print_warning(
                "Unexpected query type {} in text formatter".format(querytype))


def retrieve_object_info(session, queries, sortkey):
    """Retrieves information about data objects and collections that match
    the expanded query list."""
    results = []

    for query in queries:
        expquery = query["expanded_query"]
        qtype = query["expanded_query_type"]

        if qtype == "collection":
            queryresults = []
            queryresults.extend(get_direct_subcollections(session, expquery))
            queryresults.extend(
                get_dataobjects_in_collection(
                    session, expquery))
        elif qtype == "dataobject":
            queryresults = get_dataobject_info(session, expquery)
        else:
            exit_with_error(
                "Internal issue - illegal query type in retrieve_object_info: "
                + qtype)

        query["results"] = sort_object_info(queryresults, sortkey)
        results.append(query)

    return results


def sort_object_info(results, sortkey):
    """Sort result objects by specified key"""

    if sortkey == "unsorted":
        return results
    elif sortkey == "name":
        return sorted(results, key = lambda r : r["name"])
    elif sortkey == "ext":
        def _get_ext(n):
            # Get extension for sorting
            if n["type"] == "dataobject":
                return n["name"].split(".")[-1]
            else:
                # Use name for sorting collections
                return n["name"]

        return sorted(results, key = _get_ext )
    elif sortkey == "size":
        return sorted(results, key = lambda k: k.get("size", 0) )
    elif sortkey == "date":
        return sorted(results, key = lambda k: k.get("modify_time", 0))
    else:
        exit_with_error("Sort option {} not supported.".format(sortkey))


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
