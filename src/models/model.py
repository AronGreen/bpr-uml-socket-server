from __future__ import annotations

import json
from dataclasses import dataclass
from bson import ObjectId

from src.models.mongo_document_base import MongoDocumentBase


@dataclass
class Model(MongoDocumentBase):
    """
    Base class for all model types.
    Classes inheriting from this class must specify the field `type` with the class name in camelCase.
    In addition to the conversion methods inherited from MongoDocumentBase, a parse method is added
    that can convert json or dict into the concrete model
    """
    type = None
    path: str
    projectId: ObjectId

    @staticmethod
    def parse(data: str | dict):
        """
        Converts the given data to the correct type inferred by the `type` field in the data.
        :param data: json or dict with a representation of a subclass of Model
        :return: the parsed Model subclass
        """
        if type(data) is str:
            data = json.loads(data)
        if type(data) is not dict:
            raise TypeError
        if 'type' not in data:
            raise KeyError

        t = data['type']
        del data['type']
        # Add additional types here
        if t == TextBox.type:
            return TextBox.from_dict(data)


@dataclass
class ModelRepresentation(MongoDocumentBase):
    modelId: ObjectId
    diagramId: ObjectId
    x: float
    y: float
    w: float
    h: float


# SUBCLASSES
# remember to add type field!
@dataclass
class TextBox(Model):
    text: str
    type: str = 'textBox'


