import pytest
import simplejson
import yaml
from os import path

here = path.dirname(__file__)

with open(path.join(here, 'data', 'document.json')) \
        as in_stram:
    document = simplejson.load(in_stram)

with open(path.join(here, 'data', 'award.json')) \
        as in_stram:
    award = simplejson.load(in_stram)

with open(path.join(here, 'data', 'tender.json')) \
        as in_stram:
    tender = simplejson.load(in_stram)

with open(path.join(here, 'data', 'contract.json')) \
        as in_stram:
    contract = simplejson.load(in_stram)

with open(path.join(here, 'data', 'period.json')) \
        as in_stram:
    period = simplejson.load(in_stram)


with open(path.join(here, 'data', 'organization.json')) \
        as in_stram:
    organization = simplejson.load(in_stram)

with open(path.join(here, 'data', 'document.json')) \
        as in_stram:
    document = simplejson.load(in_stram)

with open(path.join(here, 'data', 'cancellation.json')) \
        as in_stram:
    cancellation = simplejson.load(in_stram)

with open(path.join(here, 'data', 'question.json')) \
        as in_stram:
    question = simplejson.load(in_stram)

with open(path.join(here, 'data', 'config.yaml')) \
        as in_stram:
    config = yaml.load(in_stram)
