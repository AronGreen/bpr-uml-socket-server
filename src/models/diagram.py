from dataclasses import dataclass

from bson import ObjectId

from src.models.mongo_document_base import MongoDocumentBase


@dataclass
class Diagram(MongoDocumentBase):
    title: str
    projectId: ObjectId
    path: str
    models: list  # representation object ids
