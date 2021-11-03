from dataclasses import dataclass
from typing import Optional
from src.models.mongo_document_base import MongoDocumentBase


@dataclass
class SomeItem(MongoDocumentBase):
    number: int
    text: str
    users: list
    random: Optional[str] = None


