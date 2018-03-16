from .event import Event
from schematics.models import Model
from schematics.types import ListType
from schematics.types.compound import ModelType


class EventNode(Model):
    """
    A class that implements the event traversal
    :param event : the current event
    :param children: its children event as a list
    """
    event = ModelType(Event)
    children = ListType(ModelType(Event), default=[])
