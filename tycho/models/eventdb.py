import attr
from typing import List, Dict
from .event import ignore_microseconds
from datetime import datetime


def ignore_microseconds_list(value):
    return [ignore_microseconds(d) for d in value]


@attr.s
class EventDB:
    """ This model represents event data format in DB """
    id = attr.ib(type=str)
    time = attr.ib(type=List[datetime], converter=ignore_microseconds_list)
    update_time = attr.ib(type=datetime)
    tags = attr.ib(type=List[str], default=attr.Factory(list))
    detail_urls = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
    description = attr.ib(type=str, default="")

    def asdict(self):
        eventdb_dict = attr.asdict(self)
        eventdb_dict["_id"] = eventdb_dict.pop("id")
        return eventdb_dict
