import pytest
import pytz
from datetime import datetime
from tycho.db.event.serialize import (
  _get_tags, serialize_to_db_event)
from tycho.models.event import Event, ignore_microseconds


def test_get_tags_empty_event():
    assert _get_tags({}) == []


def test_get_tags_for_tag_with_empty_array():
    """ ignore value of NoneType """
    assert _get_tags({"author": []}) == []


def test_get_tags_for_tag_field_array_with_value():
    assert _get_tags(
      {"environment": ["monitor_live", "monitor_candidate"]}) \
         == ["environment:monitor_live", "environment:monitor_candidate"]


# No error handling on code side as Event will be never passed as None.
def test_serialize_to_db_event_none_event():
    with pytest.raises(Exception):
        assert serialize_to_db_event(None)


def test_serialize_to_db_event_empty_event(patch_update_time, update_time):
    event_db_dict = serialize_to_db_event(Event())
    assert event_db_dict["tags"] == []
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_event_no_tag_field(patch_update_time, update_time):
    event_db_dict = serialize_to_db_event(Event(detail_urls="http://xyz"))
    assert event_db_dict["tags"] == []
    assert event_db_dict["detail_urls"] == "http://xyz"
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_event_tag_fields(patch_update_time, update_time):
    event_db_dict = serialize_to_db_event(Event(source_id="123"))
    assert event_db_dict["tags"] == ["source_id:123"]
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_event_tag_field_array_tag(patch_update_time,
                                                   update_time):
    event_db_dict = serialize_to_db_event(
        Event(tags={"source": ["deploy", "orchestra"]}))
    assert event_db_dict["tags"] == ["source:deploy", "source:orchestra"]
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_id(patch_update_time, update_time):
    event_db_dict = serialize_to_db_event(Event(id="507f1f77bcf86cd7994390"))
    assert event_db_dict["_id"] == "507f1f77bcf86cd7994390"
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_time_start_time(patch_update_time, update_time):
    start_time = ignore_microseconds(datetime.utcnow())
    event_db_dict = serialize_to_db_event(Event(start_time=start_time))
    assert start_time in event_db_dict["time"]
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_time_end_time(patch_update_time, update_time):
    end_time = ignore_microseconds(datetime.utcnow())
    event_db_dict = serialize_to_db_event(Event(end_time=end_time))
    assert end_time in event_db_dict["time"]
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_time_both_times(patch_update_time, update_time):
    start_time = ignore_microseconds(datetime.utcnow())
    end_time = ignore_microseconds(datetime.utcnow())
    event_db_dict = serialize_to_db_event(
        Event(start_time=start_time, end_time=end_time))
    assert event_db_dict["time"] == [start_time, end_time]
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_detail_urls_exist(patch_update_time, update_time):
    event_db_dict = serialize_to_db_event(Event(detail_urls={"http://url"}))
    assert event_db_dict["detail_urls"] == {"http://url"}
    assert event_db_dict["update_time"] == update_time


def test_serialize_to_db_detail_urls_donot_exist():
    assert serialize_to_db_event(Event()).get("detail_urls") == {}


def test_serialize_to_db_event_all_fields(app, event, eventdb, patch_update_time):
    result = serialize_to_db_event(event)
    result["tags"] = sorted(result["tags"])
    eventdb.tags = sorted(eventdb.tags)
    assert result == eventdb.asdict()
