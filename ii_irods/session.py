import json
import os
import sys
from getpass import getpass
import irods.password_obfuscation
from irods.session import iRODSSession
from ii_irods.coll_utils import get_config_filename, get_irodsA_filename
from ii_irods.utils import print_warning


def setup_session():
    """Use irods environment files to configure a iRODSSession"""

    configfile = get_config_filename()

    try:
        with open(configfile, 'r') as f:
            irods_env = json.load(f)
    except OSError:
        sys.exit("Can not find or access {}. Please use iinit".format(env_json))

    irodsAFile = get_irodsA_filename()
    try:
        with open(irodsAFile, "r") as r:
            scrambled_password = r.read()
            password = irods.password_obfuscation.decode(scrambled_password)
    except OSError:
        print_warning("Could not open {} .".format(irodsAFile))
        password = getpass(prompt="Please provide your irods password:")

    session = iRODSSession(
        host=irods_env["irods_host"],
        port=irods_env["irods_port"],
        user=irods_env["irods_user_name"],
        password=password,
        zone=irods_env["irods_zone_name"],
    )

    return session
