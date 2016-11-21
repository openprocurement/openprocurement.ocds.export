from couchdb.mapping import Document, TextField, BooleanField


class ReleaseDoc(Document):
    path = TextField()
    ocid = TextField()
    finished = BooleanField()
    _id = TextField()
