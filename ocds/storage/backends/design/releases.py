from ocds.storage.helpers import CouchView


class AllDocs(CouchView):

    design = 'docs'

    @staticmethod
    def map(doc):
        yield (doc['_id'], doc)


class OcidView(CouchView):

    design = 'ocid'

    @staticmethod
    def map(doc):
        yield (doc['ocid'], doc)


class FinishedView(CouchView):

    design = 'finished'

    @staticmethod
    def map(doc):
        if doc['finished']:
            yield (doc['ocid'], doc)


views = [
    OcidView(),
    AllDocs(),
    FinishedView()
]
