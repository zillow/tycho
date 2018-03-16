from schematics.models import Model
from schematics.types import StringType, DictType, UTCDateTimeType
from schematics.types.compound import ListType
from .types import UTCDateTimeTypeIgnoreMicroseconds


class EventDB(Model):
    """ This model represents event data format in DB """
    _id = StringType(required=True)
    tags = ListType(StringType(), required=False, serialize_when_none=False)
    time = ListType(UTCDateTimeTypeIgnoreMicroseconds(), required=True, serialize_when_none=False)  # noqa
    detail_urls = DictType(StringType(), required=False, serialize_when_none=False)  # noqa
    description = StringType(required=False, serialize_when_none=False)
    update_time = UTCDateTimeType(required=True)
