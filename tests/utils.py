import os.path
import json
from ocds.export.schema import BaseSchema
from os import listdir


def get_test_data():
    with (open(os.path.join(os.path.dirname(__file__), 'data.json'))) as ff:
        test_data = json.load(ff)
    return test_data


def get_releases(directory):
    rel = []
    for releases in listdir(directory):
        with open(directory + '/' + releases) as stream:
            data = json.load(stream)
            rel.append(data)
    return rel


test_schema = BaseSchema({
    'field': unicode,
    'value': int
})
