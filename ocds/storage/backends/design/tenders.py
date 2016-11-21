from ocds.storage.helpers import CouchView


class AllDocs(CouchView):

    design = 'docs'

    @staticmethod
    def map(doc):
        yield (doc['tenderID'], doc)


class DateView(CouchView):

    design = 'dates'

    @staticmethod
    def map(doc):
        yield (doc['dateModified'], doc)


views = [
    AllDocs(),
    DateView()
]
