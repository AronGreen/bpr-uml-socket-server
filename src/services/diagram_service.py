from __future__ import annotations

from bson import ObjectId

import src.repository as db
from src.models.diagram import Diagram
from src.models.model import FullModelRepresentation, Model


def get_diagram(diagram_id: str) -> Diagram:
    diagram = db.find_one(db.Collection.DIAGRAM, id=diagram_id)
    if diagram is not None:
        return Diagram.from_dict(diagram)

#
# def get_diagram_models(diagram_id: str | ObjectId) -> list:
#     pass
#
