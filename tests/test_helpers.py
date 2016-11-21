from utils import get_test_data
from ocds.export.helpers import get_field, make_tags, add_revisions


def test_get_field():
    tender = get_test_data()
    assert tender['tenderID'] == get_field(tender, "tenderID")
    assert tender['procuringEntity'] == get_field(tender, "buyer")


def test_tags():
    test_data = [{
        "op": "add",
        "path": "/awards/0",
        "value": "test"
    },
        {
        "op": "remove",
        "path": "/awards"
    }]
    assert (make_tags(test_data)) == set(['award', 'awardUpdate'])
    new_op = {
        "op": "add",
        "path": "/contracts/0",
        "value": "test"
    }
    test_data.append(new_op)
    assert make_tags(test_data) == set(['award', 'awardUpdate', 'contract'])
    new_op = {
        "op": "add",
        "path": "/contracts/0/value",
        "value": "test"
    }
    test_data.append(new_op)
    assert make_tags(test_data) == set(
        ['award', 'awardUpdate', 'contract', 'contractUpdate'])
    new_op = {
        "op": "add",
        "path": "/procurementMethod",
        "value": "test"
    }
    test_data.append(new_op)
    assert make_tags(test_data) == set(
        ['award', 'awardUpdate', 'contract', 'contractUpdate', 'tenderUpdate'])
    new_op = {
        "op": "replace",
        "path": "/awards/0/status",
        "value": "cancelled"
    }
    test_data.append(new_op)
    assert make_tags(test_data) == set(
        ['award', 'awardUpdate', 'contract', 'contractUpdate', 'tenderUpdate', 'awardCancellation'])


def test_revisions():
    tender1 = {
        "key": "some_value"
    }
    tender2 = {
        "key": "another_value"
    }
    tender3 = {
        "new_key": "value",
        "key": "new_value"
    }
    tenders = [tender1, tender2, tender3]
    res = add_revisions(tenders)
    assert res[0]['revisions'][0]['op'] == 'replace'
    assert res[0]['revisions'][0][
        'value'] == 'another_value'
    assert res[0]['revisions'][0]['path'] == '/key'
    assert add_revisions(tenders)[1]['revisions'][0]['op'] == 'replace'
    assert add_revisions(tenders)[1]['revisions'][0][
        'value'] == 'new_value'
    assert add_revisions(tenders)[1]['revisions'][0]['path'] == '/key'
    assert add_revisions(tenders)[1]['revisions'][1]['op'] == 'add'
    assert add_revisions(tenders)[1]['revisions'][1][
        'value'] == 'value'
    assert add_revisions(tenders)[1]['revisions'][1]['path'] == '/new_key'
