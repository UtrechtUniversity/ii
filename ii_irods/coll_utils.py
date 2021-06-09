"""This file contains utility functions related to iRODS collections."""

import os
import os.path
import pathlib

from ii_irods.do_utils import data_object_to_dict
from ii_irods.environment import get_cwd
from ii_irods.utils import print_debug

from irods.column import Like
from irods.models import Collection, DataObject, Resource


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
