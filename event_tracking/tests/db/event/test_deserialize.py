import bson
import pytest

from event_tracking.db.event.deserialize import (
    _extract_tags, _extract_time, deserialize_db_event)
from event_tracking.models.event import Event


@pytest.mark.parametrize(["input", "output"], [
    (None, {}),
    ({}, {})
])
def test_extract_tags_empty(input, output):
    assert _extract_tags(input) == output


@pytest.mark.parametrize(["input"], [
    ({"_id": "mozart_123"}),
    ({"parent_id::trigger_deploy_123"}),
    ({"parent_idtrigger_deploy_123"})
])
def test_extract_tags_untag_field(input):
    with pytest.raises(ValueError):
        assert _extract_tags(input)


def test_extract_tags_tag_field():
    assert _extract_tags(
        {"parent_id:trigger_deploy_123"}) == {
        "parent_id": "trigger_deploy_123"}


def test_extract_tags_tag_array_field():
    result = _extract_tags(
        {"environment:monitor_candidate", "environment:monitor_live",
         "action:deploy-begin", "action:deploy-host-begin",
         "action:deploy-host-end:success"}
    )
    ideal_env_tags = ["monitor_candidate", "monitor_live"]
    ideal_action_tags = [
        "deploy-begin", "deploy-host-begin", "deploy-host-end:success"
    ]
    assert sorted(result["tags"]["environment"]) == sorted(ideal_env_tags)
    assert sorted(result["tags"]["action"]) == sorted(ideal_action_tags)


@pytest.mark.parametrize(["input", "output"], [
    (None, {}),
    ({}, {}),
    ([], {}),
    (["10AM", "11AM"], {"start_time": "10AM",  "end_time": "11AM"}),
    (["10AM", "11AM"], {"start_time": "10AM",  "end_time": "11AM"}),
    (["10AM"], {"start_time": "10AM", "end_time": "10AM"})
])
def test_extract_time(input, output):
    assert _extract_time(input) == output


def test_extract_time_multiple_values():
    with pytest.raises(ValueError):
        assert _extract_time(["10AM", "11AM", "12AM"])


def test_deserialize_db_event_with_required_key():
    id = "507f1f77bcf86cd799439011"
    deserialized_event = deserialize_db_event({"_id": bson.ObjectId(id)})
    assert id == deserialized_event.id
    assert deserialized_event.start_time != None
    assert deserialized_event.end_time != None


def test_deserialize_db_event_tags_donot_exists(eventdb):
    del eventdb["tags"]
    event = {
        "id": "5498d53c5f2d60095267a0bb",
        "start_time": eventdb["time"][0],
        "end_time": eventdb["time"][1],
        "detail_urls": {
            "jira": "http://jira",
            "graphite": "http://graphite"},
        "description": "This is a trigger_deploy event.",
    }
    assert deserialize_db_event(eventdb) == Event(event)


def test_deserialize_db_event_time_exists(eventdb):
    new_eventdb = {"_id": bson.ObjectId(
        "507f1f77bcf86cd799439011"), "time": [
        eventdb["time"][0], eventdb["time"][1]]}
    new_event = {
        "start_time": eventdb["time"][0],
        "end_time": eventdb["time"][1],
        "id": "507f1f77bcf86cd799439011"
    }
    assert deserialize_db_event(new_eventdb) == Event(new_event)


def test_deserialize_db_event_detail_urls_not_exist():
    new_eventdb = {"_id": bson.ObjectId("507f1f77bcf86cd799439011")}
    assert "detail_urls" not in deserialize_db_event(new_eventdb).to_native()


def test_deserialize_db_event_detail_urls_exist():
    new_eventdb = {"_id": bson.ObjectId("507f1f77bcf86cd799439011"),
                   "detail_urls": {"graphite": "http://graphite"}}
    assert "detail_urls" in deserialize_db_event(new_eventdb).to_native()


def test_deserialize_db_event_all_fields(event, eventdb):
    assert deserialize_db_event(eventdb) == event
