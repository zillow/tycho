from datetime import datetime
from ...models.event import Event
from typing import Dict, List


def serialize_to_db_event(event: Event) -> Dict:
    """
    Transforms public event format to DB event format.
    Ignores key and value with NoneType.
    """

    new_event = {}

    new_event["tags"] = []

    if event.tags is not None:
        new_event["tags"].extend(_get_tags(event.tags))

    for key in ["source_id", "parent_id"]:
        if getattr(event, key):
            new_event["tags"].append(
                "{key}:{value}".format(key=key, value=getattr(event, key)))

    if event.id is not None:
        new_event["_id"] = str(event.id)

    new_event["time"] = []

    for key in ["start_time", "end_time"]:
        if getattr(event, key) is not None:
            new_event["time"].append(getattr(event, key))

    for key in ["detail_urls", "description"]:
        if getattr(event, key) is not None:
            new_event[key] = getattr(event, key)

    new_event["update_time"] = datetime.utcnow()

    return new_event


def _get_tags(event_tags: Dict) -> List:
    """
    Transforms dictionary of key-value pairs (not in untag_fields list)
    to list of key-value pair concatenated as strings inside tags field.
    """
    tags = []

    # event_tags will be an empty dictionary by default.
    # key and value in event_tags will never be of None Type.
    for key in event_tags:
        for value in event_tags[key]:
            tags.append(
             "{key}:{value}".format(key=key, value=value))

    return tags
