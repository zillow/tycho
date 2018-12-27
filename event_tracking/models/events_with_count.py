import attr
from typing import List
from .event import Event


@attr.s
class EventListWithCount:
    """
    :param result : the list of events
    :param count : the number of events in result
    """
    count = attr.ib(type=int)
    result = attr.ib(type=List[Event], default=attr.Factory(list))
