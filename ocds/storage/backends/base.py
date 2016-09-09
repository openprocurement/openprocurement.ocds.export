

class Storage(object):

    def __init__(self, url):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    def __contains__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        pass
        raise NotImplementedError

    def __delitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

    def save(self, key, value):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def query(self, start_key, end_key, **options):
        raise NotImplementedError
