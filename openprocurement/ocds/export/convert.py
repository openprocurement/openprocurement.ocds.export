import jsonpatch
from .helpers import patch_converter


class Converter(object):

    @classmethod
    def _convert(cls, raw_data):
        return cls(raw_data).serialize()

    @classmethod
    def fromDiff(cls, prev, new):
        amendment = {}
        patch = jsonpatch.make_patch(cls._convert(new), cls._convert(prev)).patch
        if patch:
            amendment['changes'] = patch_converter(patch)
            amendment['date'] = new.get('dateModified') if 'dateModified' in new else new.get('date')
            new['amendment'] = amendment
            return cls(new)
        return ''
