from ocds.storage.helpers import CouchView


class AllDocs(CouchView):

    design = 'docs'

    @staticmethod
    def map(doc):
        if 'doc_type' in doc and doc['doc_type'] != 'Tender':
            return

        yield doc['_id'], doc


class DateView(CouchView):

    design = 'dates'

    @staticmethod
    def map(doc):
        if 'doc_type' in doc and doc['doc_type'] != 'Tender':
            return

        yield doc['_id'], doc['dateModified']


views = [
    AllDocs(),
    DateView()
]
