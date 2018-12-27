import attr
from typing import List
from .event import Event, CATTRS_CONVERTER


@attr.s
class EventNode:
    """
    A class that implements the event traversal
    :param event : the current event
    :param children: its children event as a list
    """
    event = attr.ib(type=Event)
    children = attr.ib(type=List[Event], default=attr.Factory(list))

    def to_primitive(self):
        return CATTRS_CONVERTER.unstructure(self)
