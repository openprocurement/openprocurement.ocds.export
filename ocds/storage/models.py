from couchdb.mapping import Document, TextField, BooleanField


class ReleaseDoc(Document):
    path = TextField()
    finished = BooleanField()
    _id = TextField()
    date = TextField()
