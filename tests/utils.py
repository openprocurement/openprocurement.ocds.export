import os.path
import json
from ocds.export.schema import BaseSchema

def get_test_data():
    with (open(os.path.join(os.path.dirname(__file__), 'data.json'))) as ff:
        test_data = json.load(ff)
    return test_data


test_schema = BaseSchema({
    'field': unicode,
    'value': int
})
