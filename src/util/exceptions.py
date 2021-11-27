class RepositoryException(Exception):
    def __init__(self):
        super(RepositoryException, self).__init__()


class DocumentNotFoundException(RepositoryException):
    def __init__(self, requested_document_id):
        self.requested_document_id = requested_document_id
        super(DocumentNotFoundException, self).__init__()


class ListItemNotFoundException(RepositoryException):
    def __init__(self, document_id, list_field, item_identifier):
        self.document_id = document_id
        self.list_field = list_field
        super(ListItemNotFoundException, self).__init__()


class MissingPropertyException(Exception):
    def __init__(self, property):
        self.property = property
        super(MissingPropertyException, self).__init__(f'Missing property: {self.property}')