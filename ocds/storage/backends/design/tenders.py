from ocds.storage.helpers import CouchView


class AllDocs(CouchView):

    design = 'docs'

    @staticmethod
    def map(doc):
        yield (doc['id'], doc)


views = [
    AllDocs()
]
