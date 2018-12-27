import attr
import pytz
from bson import ObjectId
from datetime import datetime
from uuid import uuid4
from typing import Dict, List
from transmute_core.object_serializers.cattrs_serializer import create_cattrs_converter


CATTRS_CONVERTER = create_cattrs_converter()


def ensure_value_is_not_empty(instance, attribute, value):
    if not value:
        raise ValueError("Values must not be none or empty")
    return value


def ensure_maxlength_100_chars_and_tags_key_val_not_none(instance, attribute, value):
    """
    A helper function to ensure that the values for
    the reserved kays are less than a hundred character limit
    and that the tags do not have any none keys or vals
    """
    if isinstance(value, str):
        if len(value) > 100:
            raise ValueError("Values must not "
                             "exceed length of 100 chars")
    elif isinstance(value, dict):
        for key in value:
            if key is None or key == "None":
                raise ValueError("Tags keys can't be None")
            if value.get(key) is None:
                raise ValueError("Tags values can't be None")
            for elem in value[key]:
                if elem is None:
                    raise ValueError("Tags values can't be None")
                if len(elem) > 100:
                    raise ValueError("Values must not "
                                     "exceed length of 100 chars")
    return value


def ensure_value_is_not_none(instance, attribute, value):
    """
    A helper function to ensure that the values for
    the time is not none
    """
    if value is None:
        raise ValueError("Value can't be None")


def ignore_microseconds(value):
    if value.tzinfo is None:
        utc = pytz.timezone('UTC')
        value = utc.localize(value)
    value = value.astimezone(pytz.utc)
    microsecond = value.microsecond
    new_microsecond = int(microsecond / 1000) * 1000
    return value.replace(microsecond=new_microsecond)


@attr.s
class Event(object):
    """
    This class defines an event with the following reserved fields:
        id,
        source_id,
        parent_id,
        start_time,
        end_time,
        description,
        detail_urls

    and allows other optional attributes to be added depending on the type
    of the event that go inside the tags field.

    An example of an event as a json object is:
    {
       "id": "333f1f77bcf86cd799439011"
       "source_id": "222f1f77bcf86cd799439011",
       "parent_id": "111f1f77bcf86cd799439011",
       "start_time": "12/05/16:10:25:00",
       "end_time": "12/05/16:10:26:00",
       "description": "This is a deploy deployment",
       "detail_urls": {"graphite": "http//graphite"}
       "tags": {
                  "source": ["deploy"],
                  "type": ["deploy/deploy_all"],
                  "author": ["user@example.com", "user2@example.com"],
                  "environment": ["monitor_candidate"],
                  "services": ["tycho"],
                  "status": ["success"]
                }
    }
    """
    # reserved keys
    # assign uuid as id for event if not provided
    id = attr.ib(type=str, default=attr.Factory(lambda: str(uuid4())),
                 validator=[ensure_value_is_not_empty, ensure_maxlength_100_chars_and_tags_key_val_not_none])
    source_id = attr.ib(type=str, default="",
                        validator=[ensure_maxlength_100_chars_and_tags_key_val_not_none])
    parent_id = attr.ib(type=str, default="",
                        validator=[ensure_maxlength_100_chars_and_tags_key_val_not_none])
    start_time = attr.ib(type=datetime, default=attr.Factory(datetime.utcnow),
                         converter=ignore_microseconds, validator=[ensure_value_is_not_none])
    end_time = attr.ib(type=datetime, default=attr.Factory(datetime.utcnow),
                       converter=ignore_microseconds, validator=[ensure_value_is_not_none])
    description = attr.ib(type=str, default="")
    detail_urls = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
    tags = attr.ib(type=Dict[str, List[str]], default=attr.Factory(dict),
                   validator=[ensure_maxlength_100_chars_and_tags_key_val_not_none])

    @staticmethod
    def from_dict(d):
        return CATTRS_CONVERTER.structure(d, Event)

    def to_primitive(self):
        return CATTRS_CONVERTER.unstructure(self)
