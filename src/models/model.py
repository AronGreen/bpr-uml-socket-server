import json
from dataclasses import dataclass
from bson import ObjectId
from dataclasses_json import dataclass_json, Undefined

from src.models.mongo_document_base import MongoDocumentBase


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Model(MongoDocumentBase):
    """
    Base class for all model types.
    Classes inheriting from this class must specify the field `type` with the class name in camelCase.
    In addition to the conversion methods inherited from MongoDocumentBase, a parse method is added
    that can convert json or dict into the concrete model
    """
    type = None

    projectId: ObjectId
    folderId: ObjectId

    @staticmethod
    def parse(data):
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
            return TextBox.from_dictionary(data)


@dataclass
class Representation(MongoDocumentBase):
    modelId: ObjectId
    x: str
    y: str
    w: str
    h: str


@dataclass
class TextBox(Model):
    text: str
    type: str = 'textBox'


