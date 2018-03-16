from collections import defaultdict

from event_tracking.models.eventdb import EventDB
from event_tracking.models.event import Event
from typing import Dict, List


_reserved_fields_in_eventdb_tag = {
    "source_id", "parent_id"
}


def deserialize_db_event(eventdb: EventDB) -> Event:
    """
    Transforms DB event format to Public event format
    """
    new_event = {}

    if eventdb:

        if "tags" in eventdb:
            new_event.update(_extract_tags(eventdb["tags"]))

        if "time" in eventdb:
            new_event.update(_extract_time(eventdb["time"]))

        if "_id" in eventdb:
            new_event["id"] = str(eventdb["_id"])

        if "detail_urls" in eventdb:
            new_event["detail_urls"] = eventdb["detail_urls"]

        if "description" in eventdb:
            new_event["description"] = eventdb["description"]

    return Event(new_event)


def _extract_tags(tags: Dict) -> Dict:
    """
    Transforms list of key-value pair as strings to a
    dictionary of key-value pairs.
    """
    new_event = {}
    tagged_fields = defaultdict(list)

    if tags:
        for doc in tags:
            key, value = doc.split(':', 1)
            # not a tag key
            if key in _reserved_fields_in_eventdb_tag:
                new_event[key] = value
            # key already present, no need to initialize.
            else:
                tagged_fields[key].append(value)

    if len(tagged_fields) > 0:
        new_event["tags"] = tagged_fields

    return new_event


def _extract_time(time: List) -> Dict:
    """
    Transforms array of times to dictionary of start and end time.
    """

    if not time:
        return {}
    elif len(time) > 2:
        raise ValueError("should not have 3 times : {time}".format(time=time))
    elif len(time) == 2:
        return {"start_time": time[0], "end_time": time[1]}
    elif len(time) == 1:
        return {"start_time": time[0], "end_time": time[0]}
