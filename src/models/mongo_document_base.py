from dataclasses import dataclass, asdict, fields
from bson.objectid import ObjectId
import json


# noinspection PyArgumentList
@dataclass
class SimpleMongoDocumentBase:
    """
    Represents a base mongo document.
    Provides conversion methods to and from dict and json.
    Ensures proper conversion between ObjectId and str as needed.
    """
    def as_dict(self):
        return asdict(self)

    def as_json(self):
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_dict(cls, dic: dict):
        return cls(**dic)

    @classmethod
    def as_dict_list(cls, lst: list):
        return [ob.as_dict() for ob in lst]

    @classmethod
    def as_json_list(cls, lst: list):
        return json.dumps(cls.as_dict_list(lst), default=str)

    @classmethod
    def from_json_list(cls, json_list):
        return cls.from_dict_list(json.loads(json_list))

    @classmethod
    def from_dict_list(cls, lst: list):
        return [cls.from_dict(x) for x in lst]

    @classmethod
    def from_json(cls, j: str):
        return cls(**json.loads(j))

    def get_fields(self):
        return fields(self)

    def __post_init__(self):
        for field in fields(self):
            if isinstance(field.type, ObjectId):
                attr = getattr(self, field.name)
                if attr is not None and isinstance(attr, str):
                    setattr(self, field.name, ObjectId(attr))


@dataclass
class MongoDocumentBase(SimpleMongoDocumentBase):
    """
    Represents a base mongo document with an _id property.
    Provides conversion methods to and from dict and json.
    Ensures proper conversion between ObjectId and str as needed.
    """
    _id: ObjectId()

    @property
    def id(self):
        return self._id
