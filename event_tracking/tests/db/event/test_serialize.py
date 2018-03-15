import pytest
from event_tracking.db.event.serialize import (
  _get_tags, serialize_to_db_event)


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
    assert serialize_to_db_event({}) == {"tags": [], "time": [],
                                         "update_time": update_time}


def test_serialize_to_db_event_no_tag_field(patch_update_time, update_time):
    assert serialize_to_db_event(
      {"detail_urls": "http://xyz"}) == {
         "tags": [], "detail_urls": "http://xyz", "time": [],
         "update_time": update_time}


def test_serialize_to_db_event_tag_fields(patch_update_time, update_time):
    assert serialize_to_db_event(
      {"source_id": "123"}) == {"tags": ["source_id:123"], "time": [],
                                "update_time": update_time}


def test_serialize_to_db_event_tag_field_array_no_tag(patch_update_time,
                                                      update_time):
    assert serialize_to_db_event(
      {"source": ["mozart", "orchestra"]}) == {"tags": [], "time": [],
                                               "update_time": update_time}


def test_serialize_to_db_event_none_field_value(patch_update_time, update_time):
    assert serialize_to_db_event({None: None}) == {"tags": [], "time": [],
                                                   "update_time": update_time}


def test_serialize_to_db_event_tag_field_array_tag(patch_update_time,
                                                   update_time):
    assert serialize_to_db_event(
      {"tags": [], "tags": {"source": ["mozart", "orchestra"]}}) == {
       "tags": ["source:mozart", "source:orchestra"], "time": [],
       "update_time": update_time}


def test_serialize_to_db_id(patch_update_time, update_time):
    assert serialize_to_db_event(
      {"id": "507f1f77bcf86cd7994390"}) == {
        "_id": "507f1f77bcf86cd7994390",
        "tags": [], "time": [], "update_time": update_time}


def test_serialize_to_db_time_start_time(patch_update_time, update_time):
    assert serialize_to_db_event(
      {"start_time": "10AM"}) == {"tags": [], "time": ["10AM"],
                                  "update_time": update_time}


def test_serialize_to_db_time_end_time(patch_update_time, update_time):
    assert serialize_to_db_event(
      {"end_time": "11AM"}) == {"tags": [], "time": ["11AM"],
                                "update_time": update_time}


def test_serialize_to_db_time_both_times(patch_update_time, update_time):
    assert serialize_to_db_event(
      {"start_time": "10AM", "end_time": "11AM"}) == {
          "tags": [], "time": ["10AM", "11AM"], "update_time": update_time}


def test_serialize_to_db_detail_urls_exist(patch_update_time, update_time):
    assert serialize_to_db_event(
      {"detail_urls": {"http://url"}}) == {
          "tags": [], "detail_urls": {"http://url"}, "time": [],
          "update_time": update_time}


def test_serialize_to_db_detail_urls_donot_exist():
    assert "detail_urls" not in serialize_to_db_event({})


def test_serialize_to_db_event_all_fields(app, event, eventdb, patch_update_time):
    result = serialize_to_db_event(event)
    result["tags"] = sorted(result["tags"])
    eventdb["tags"] = sorted(eventdb["tags"])
    assert result == eventdb
