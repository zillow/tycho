from .event import Event
from schematics.models import Model
from schematics.types import ListType, IntType
from schematics.types.compound import ModelType


class EventListWithCount(Model):
    """
    :param result : the list of events
    :param count : the number of events in result
    """
    result = ListType(ModelType(Event), default=[])
    count = IntType()
