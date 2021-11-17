from __future__ import annotations

from bpr_data.repository import Repository, Collection
from bpr_data.models.diagram import Diagram

import settings


db = Repository.get_instance(
    protocol=settings.MONGO_PROTOCOL,
    default_db=settings.MONGO_DEFAULT_DB,
    pw=settings.MONGO_PW,
    host=settings.MONGO_HOST,
    user=settings.MONGO_USER)


def get_diagram(diagram_id: str) -> Diagram:
    diagram = db.find_one(Collection.DIAGRAM, id=diagram_id)
    if diagram is not None:
        return Diagram.from_dict(diagram)

#
# def get_diagram_models(diagram_id: str | ObjectId) -> list:
#     pass
#
