from dataclasses import dataclass
from typing import Optional

from bson import ObjectId

from src.models.mongo_document_base import MongoDocumentBase


@dataclass
class Diagram(MongoDocumentBase):
    title: str
    projectId: ObjectId
    models: list  # representations
