from bson import ObjectId
from datetime import datetime
from uuid import uuid4
from schematics.exceptions import ValidationError
from schematics.models import Model
from schematics.types import StringType
from schematics.types.compound import ListType, DictType

from .types import UTCDateTimeTypeIgnoreMicroseconds


def ensure_maxlength_100_chars_and_tags_key_val_not_none(value):
    """
    A helper function to ensure that the values for
    the reserved kays are less than a hundred character limit
    and that the tags do not have any none keys or vals
    """
    if isinstance(value, str):
        if len(value) > 100:
            raise ValidationError("Values must not "
                                  "exceed length of 100 chars")
    elif isinstance(value, dict):
        for key in value:
            if key is None or key == "None":
                raise ValidationError("Tags keys can't be None")
            if value.get(key) is None:
                raise ValidationError("Tags values can't be None")
            for elem in value[key]:
                if elem is None:
                    raise ValidationError("Tags values can't be None")
                if len(elem) > 100:
                    raise ValidationError("Values must not "
                                          "exceed length of 100 chars")
    return value


def ensure_value_is_not_none(value):
    """
    A helper function to ensure that the values for
    the time is not none
    """
    if value is None:
        raise ValidationError("Value can't be None")
    return value


class Event(Model):
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
       "description": "This is a Mozart deployment",
       "detail_urls": {"graphite": "http//graphite"}
       "tags": {
                  "source": ["mozart"],
                  "type": ["deploy/deploy_all"],
                  "author": ["yusuket@zillow.com", "saroj@zillow.com"],
                  "environment": ["monitor_candidate"],
                  "services": ["zon-web"],
                  "status": ["success"]
                }
    }
    """
    # reserved keys
    # assign uuid as id for event if not provided
    id = StringType(
        validators=[
            ensure_maxlength_100_chars_and_tags_key_val_not_none, ensure_value_is_not_none],
        required=True, default=lambda: str(uuid4()), serialize_when_none=False)
    source_id = StringType(
        validators=[ensure_maxlength_100_chars_and_tags_key_val_not_none],
        required=False, serialize_when_none=False)
    parent_id = StringType(
        validators=[ensure_maxlength_100_chars_and_tags_key_val_not_none],
        required=False, serialize_when_none=False)
    start_time = UTCDateTimeTypeIgnoreMicroseconds(
        validators=[ensure_value_is_not_none],
        required=True, default=lambda: datetime.utcnow(), serialize_when_none=False)
    end_time = UTCDateTimeTypeIgnoreMicroseconds(
        validators=[ensure_value_is_not_none],
        required=True, default=lambda: datetime.utcnow(), serialize_when_none=False)
    description = StringType(
        required=False, serialize_when_none=False)
    detail_urls = DictType(
        StringType(), required=False,
        serialize_when_none=False)

    # non-reserved keys
    tags = DictType(
        ListType(StringType()),
        validators=[ensure_maxlength_100_chars_and_tags_key_val_not_none],
        required=False, default=dict(), serialize_when_none=False)
