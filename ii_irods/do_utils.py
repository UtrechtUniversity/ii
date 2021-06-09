"""Utility functions for dealing with data objects"""
import os

from irods.models import Collection, DataObject, Resource


def dataobject_exists(session, path):
    '''Returns a boolean value that indicates whether a data object with the provided name exists.'''
    collection_name, dataobject_name = os.path.split(path)
    return len(list(session.query(Collection.name, DataObject.name).filter(
        DataObject.name == dataobject_name).filter(
        Collection.name == collection_name).get_results())) > 0


def get_dataobject_info(session, path):
    """Returns information about a data object in a list of dictionaries"""
    collection_name, dataobject_name = os.path.split(path)
    qresult = session.query(Collection.name, DataObject.name, DataObject.size,
                            DataObject.modify_time, DataObject.replica_number,
                            DataObject.replica_status, DataObject.checksum, DataObject.path,
                            DataObject.id, DataObject.owner_zone, DataObject.owner_name,
                            Resource.name).filter(
        Collection.name == collection_name, DataObject.name == dataobject_name
    ).get_results()
    return list(map(data_object_to_dict, qresult))


def data_object_to_dict(d):
    return {
        "type": "dataobject",
        "collection": d[Collection.name],
        "name": d[DataObject.name],
        "full_name": "{}/{}".format(d[Collection.name], d[DataObject.name]),
        "size": d[DataObject.size],
        "modify_time": d[DataObject.modify_time].timestamp(),
        "replica_number": d[DataObject.replica_number],
        "replica_status": d[DataObject.replica_status],
        "resc_name": d[Resource.name],
        "physical_path": d[DataObject.path],
        "checksum": d[DataObject.checksum],
        "id": d[DataObject.id],
        "owner_name": d[DataObject.owner_name],
        "owner_zone": d[DataObject.owner_zone]}
