class RepositoryException(Exception):
    def __init__(self):
        super(RepositoryException, self).__init__()


class DocumentNotFoundException(RepositoryException):
    def __init__(self, requested_document_id):
        self.requested_document_id = requested_document_id
        super(DocumentNotFoundException, self).__init__()


class ListItemNotFoundException(Exception):
    def __init__(self, document_id, list_field, item_identifier):
        self.document_id = document_id
        self.list_field = list_field
        self.item_identifier = item_identifier
        super(ListItemNotFoundException, self).__init__(f'doc:{self.document_id},field:{self.list_field},identifier:{self.item_identifier}')


class MissingPropertyException(Exception):
    def __init__(self, prop):
        self.prop = prop
        super(MissingPropertyException, self).__init__(f'Missing property: {self.prop}')
