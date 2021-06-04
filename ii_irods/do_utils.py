"""Utility functions for dealing with data objects"""
import os
from irods.models import Collection, DataObject


def dataobject_exists(session, path):
    '''Returns a boolean value that indicates whether a data object with the provided name exists.'''
    collection_name, dataobject_name = os.path.split(path)
    return len(list(session.query(Collection.name, DataObject.name).filter(
        DataObject.name == dataobject_name).filter(
        Collection.name == collection_name).get_results())) > 0
