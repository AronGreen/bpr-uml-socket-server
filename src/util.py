from bson import ObjectId


def ensure_object_id(data) -> ObjectId:
    _id = data
    if type(data) == str:
        _id = ObjectId(data)
    if type(_id) is not ObjectId:
        raise TypeError
    return _id
