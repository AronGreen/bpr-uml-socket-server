from dataclasses import dataclass
from typing import Optional
from src.models.mongo_document_base import MongoDocumentBase


@dataclass
class Project(MongoDocumentBase):
    title: str

