from tortoise import Model
from tortoise.fields import *
from enum import Enum


class StatusEnum(Enum):
    COMPLETED = 'completed'
    PROGRESS = 'progress'
    PENDING = 'pending'


class User(Model):
    id = IntField(pk=True)
    username = CharField(25, unique=True)
    password = TextField()
    current_access_token = CharField(36, unique=True, null=True)
    reference = CharField(36, unique=True)


class Task(Model):
    id = IntField(pk=True)
    task = CharField(55, unique=True)
    reference = CharField(36, unique=True)
    description = CharField(255)
    status = CharEnumField(StatusEnum)
    user = ForeignKeyField('models.User', related_name='tasks')
