from ocds.storage.helpers import CouchView


class OcidView(CouchView):

    design = 'ocid'

    @staticmethod
    def map(doc):
        yield (doc['ocid'], doc)


class TagView(CouchView):

    design = 'tags'

    @staticmethod
    def map(doc):
        yield (doc['ocid'], doc['tag'])


class DateView(CouchView):

    design = 'date'

    @staticmethod
    def map(doc):
        yield (doc['date'], doc)


views = [
    OcidView(),
    TagView(),
    DateView()
]
