import json
import os
import os.path
import pathlib
import psutil

from ii_irods.do_utils import data_object_to_dict
from ii_irods.utils import print_debug

from irods.column import Like
from irods.models import Collection, DataObject, Resource


def get_cwd(verbose=False):
    """Returns current working directory (collection) in iRODS"""

    sessionfile = get_session_filename()

    if os.path.exists(sessionfile):
        if verbose:
            print_debug("Session file exists. Looking up CWD in session file.")
        with open(sessionfile) as f:
            data = json.load(f)
            if "irods_cwd" in data:
                return data["irods_cwd"]
            elif verbose:
                print_debug("CWD not found in session file. Falling back to " +
                            "config.")
    else:
        if verbose:
            print_debug(
                "No session file found. Retrieving CWD from config file.")

    configfile = get_config_filename()

    if os.path.exists(configfile):
        with open(configfile) as f:
            data = json.load(f)
            if "irods_cwd" in data:
                if verbose:
                    print_debug("CWD retrieved from config file.")
                return data["irods_cwd"]
            else:
                if verbose:
                    print_debug(
                        "CWD not found in config file. Falling backing to homedir.")
                return get_home(verbose)
    else:
        raise Exception("Config file not found.")


def get_home(verbose=False):
    """Returns home directory of current user"""
    configfile = get_config_filename()

    if os.path.exists(configfile):
        with open(configfile) as f:
            data = json.load(f)

            if "irods_home" in data:
                return data["irods_home"]
            elif "irods_zone_name" in data and "irods_user_name" in data:
                if verbose:
                    print_debug(
                        "CWD and home undefined. Returning default homedir.")
                return "{}/home/{}".format(data["irods_zone_name"],
                                           data["irods_user_name"])
            else:
                raise Exception(
                    "Unable to determine CWD. CWD or homedir variables not found.")


def set_cwd(directory, verbose=False):
    """Sets working directory (collection) in session. Parameter must be an absolute iRODS path."""

    sessionfile = get_session_filename()

    if os.path.exists(sessionfile):
        if verbose:
            print_debug(
                "Storing CWD in existing session file {} ...".format(sessionfile))

        with open(sessionfile, "r+") as f:
            data = json.load(f)
            data["irods_cwd"] = directory
            f.seek(0)
            json.dump(data, f)
            f.truncate()
    else:
        if verbose:
            print_debug(
                "Storing CWD in new session file {} ...".format(sessionfile))

        with open(sessionfile, "w+") as f:
            data = { "irods_cwd": directory }
            json.dump(data, f)


def resolve_base_path(relativepath, basepath):
    """"Converts a relative path plus an absolute base path to a
    single absolute path"""
    p = pathlib.Path(os.path.join(basepath, relativepath))
    return str(p.resolve())


def convert_to_absolute_path(path):
    """Converts a relative path to an absolute path (if an absolute path
    is supplied the argument is returned unchanged.)"""
    if os.path.isabs(path):
        return path
    else:
        return resolve_base_path(path, get_cwd())


def get_session_filename():
    """Returns the session filename."""
    ppid = psutil.Process(os.getpid()).ppid()
    return os.path.expanduser("~/.irods/irods_environment.json." + str(ppid))


def get_config_filename():
    """Returns the configuration filename"""
    return os.path.expanduser("~/.irods/irods_environment.json")


def get_irodsA_filename():
    """Returns the scrambled password filename"""
    return os.path.expanduser("~/.irods/.irodsA")


def verify_environment(check_auth=True):
    """Verifies iRODS configuration. Returns boolean that says whether the
    iRODS configuration is correct, as well as a list of issues. """

    configfile = get_config_filename()

    if not os.path.exists(configfile):
        return False, ["iRODS configuration file not found."]

    with open(configfile) as f:
        config = json.load(f)
        requiredfields = ["irods_host", "irods_port", "irods_user_name",
                          "irods_zone_name"]
        missingfields = []

        for field in requiredfields:
            if field not in config:
                missingfields.append(field)

        if len(missingfields) > 0:
            return False, map(lambda f:
                              "configuration is missing entry for " + f,
                              missingfields)

    spfile = get_irodsA_filename()

    if check_auth and not os.path.exists(spfile):
        return False, ["Please use iinit to log in to iRODS first"]

    return True, []


def collection_exists(session, collection):
    '''Returns a boolean value that indicates whether a collection with the provided name exists.'''
    return len(list(session.query(Collection.name).filter(
        Collection.name == collection).get_results())) > 0


def get_dataobjects_in_collection(session, collection):
    """Returns a list of dictionaries with properties of data objects in the
    provided collection."""
    qresult = session.query(Collection.name, DataObject.name, DataObject.size,
              DataObject.modify_time, DataObject.replica_number,
              DataObject.replica_status, DataObject.checksum, DataObject.path,
              DataObject.id, DataObject.owner_zone, DataObject.owner_name,
              Resource.name).filter(
              Collection.name == collection
              ).get_results()
    return list(map(data_object_to_dict, qresult))


def get_direct_subcollections(session, collection):
    """Returns a list of subcollections one level below the provided
    collection."""
    qresult = session.query(Collection.name, Collection.modify_time, Collection.id,
            Collection.parent_name, Collection.owner_name, Collection.owner_zone).filter(
            Collection.parent_name == collection).get_results()
    return list(map(coll_object_to_dict, qresult))


def coll_object_to_dict(c):
    """Utility function to convert an iRODS-client Collection to a dictionary"""
    return {
        "type": "collection",
        "name": c[Collection.name],
        "id": c[Collection.id],
        "parent_name": c[Collection.parent_name],
        "modify_time": c[Collection.modify_time].timestamp(),
        "owner_name": c[Collection.owner_name],
        "owner_zone": c[Collection.owner_zone]
    }


def get_subcollections(session, collection):
    """Get a list of the names of all subcollections (irrespective of depth) of a collection"""

    if collection.endswith("/"):
        searchstring = "{}%%".format(collection)
    else:
        searchstring = "{}/%%".format(collection)

    subcollections = session.query(Collection.name).filter(
        Like(Collection.name, searchstring)).get_results()

    return list(map(lambda d: d[Collection.name], subcollections))
