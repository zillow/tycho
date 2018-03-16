from schematics.types import UTCDateTimeType


class UTCDateTimeTypeIgnoreMicroseconds(UTCDateTimeType):

    """
       A variant of ``UTCDateTimeTypeExt`` that stores time
       granularity in milliseconds instead of microseconds.
    """

    def __init__(self, formats=None, **kwargs):
        super(UTCDateTimeType, self).__init__(
            formats=formats, convert_tz=True, drop_tzinfo=True, **kwargs
        )

    def _ignore_microseconds(self, value):
        microsecond = value.microsecond
        new_microsecond = int(microsecond / 1000) * 1000
        return value.replace(microsecond=new_microsecond)

    def to_primitive(self, value, context=None):
        new_dt = self._ignore_microseconds(value)
        return super(UTCDateTimeType, self).to_primitive(new_dt, context)

    def to_native(self, value, context=None):
        old_dt = super(UTCDateTimeType, self).to_native(value, context)
        return self._ignore_microseconds(old_dt)

    def from_string(self, value):
        old_dt = super(UTCDateTimeType, self).from_string(value)
        if old_dt is None:
            return None
        else:
            return self._ignore_microseconds(old_dt)

    def _mock(self, context=None):
        old_dt = super(UTCDateTimeType, self)._mock(context)
        return self._ignore_microseconds(old_dt)

    def pre_setattr(self, value):
        return self._ignore_microseconds(value)    # pragma: no cover
