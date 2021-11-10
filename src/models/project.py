from dataclasses import dataclass
from bson.objectid import ObjectId
from src.models.mongo_document_base import MongoDocumentBase, SimpleMongoDocumentBase


@dataclass
class Project(MongoDocumentBase):
    title: str
    workspaceId: ObjectId
    users: list  # ProjectUser
    teams: list  # ProjectTeam


@dataclass
class ProjectUser(SimpleMongoDocumentBase):
    userId: ObjectId
    isEditor: bool


@dataclass
class ProjectTeam(SimpleMongoDocumentBase):
    teamId: ObjectId
    isEditor: bool
