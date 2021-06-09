import json
import os
import os.path
import psutil

from ii_irods.utils import print_debug, get_ppid

"""This file contains functions related to the local environment configuration,
   session file and scrambled password file."""


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
            data = {"irods_cwd": directory}
            json.dump(data, f)


def get_session_filename():
    """Returns the session filename."""
    return os.path.expanduser(
        "~/.irods/irods_environment.json." + str(get_ppid()))


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
