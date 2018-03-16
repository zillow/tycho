from datetime import datetime, timedelta
import json
from unittest.mock import patch
import pytest

from aiohttp.web import HTTPNotFound
from event_tracking.routes.event import _merge, _update
from event_tracking.models.event import Event
from schematics.exceptions import DataError


async def test_get_event(event_in_db, cli):
    resp = await cli.get('/api/v1/event/{0}'.format(
        event_in_db.id
    ))
    retrieved_event_json = (await resp.json())
    retrieved_event = Event(retrieved_event_json)
    assert (retrieved_event.to_primitive() ==
            event_in_db.to_primitive())
    assert resp.status == 200


async def test_get_children_events(event_in_db, cli):
    resp = await cli.get('/api/v1/event/{0}/children'.format(
        event_in_db["parent_id"]
    ))
    retrieved_event_json = (await resp.json())
    retrieved_event = Event(retrieved_event_json[0])
    assert (retrieved_event.to_primitive() ==
            event_in_db.to_primitive())
    assert resp.status == 200


async def test_get_event_with_no_query_parameters(source_event_in_db,
                                                  parent_event_in_db,
                                                  event_in_db,
                                                  cli):
    resp = await cli.get('/api/v1/event/')
    assert resp.status == 200

    retrieved_event_json = (await resp.json())
    assert retrieved_event_json["result"][0] == \
        source_event_in_db.to_primitive()
    assert retrieved_event_json["result"][2] == \
        event_in_db.to_primitive()
    assert retrieved_event_json["count"] == 3


async def test_get_event_with_page_parameters(source_event_in_db,
                                              parent_event_in_db,
                                              event_in_db,
                                              cli):
    resp = await cli.get('/api/v1/event/?page=1')
    assert resp.status == 200

    retrieved_event_json = (await resp.json())
    assert retrieved_event_json["result"][0] == \
           source_event_in_db.to_primitive()
    assert retrieved_event_json["result"][2] == \
           event_in_db.to_primitive()
    assert retrieved_event_json["count"] == 3

    # page 2
    resp = await cli.get('/api/v1/event/?page=2')
    assert resp.status == 200

    retrieved_event_json = (await resp.json())
    assert retrieved_event_json["count"] == 0


async def test_get_events_with_timestamp_queries(parent_event_in_db,
                                                 event_in_db,
                                                 cli):
    frm = parent_event_in_db.start_time.isoformat()
    to = event_in_db.start_time.isoformat()
    resp = await cli.get('/api/v1/event/?frm={0}&to={1}'.format(frm, to))
    event_json = (await resp.json())
    assert event_json["count"] == 2
    assert parent_event_in_db.to_primitive() == event_json["result"][1]

    to = (event_in_db.start_time + timedelta(seconds=1)).isoformat()
    resp = await cli.get('/api/v1/event/?frm={0}&to={1}'.format(frm, to))
    event_json = (await resp.json())
    assert event_json["count"] == 3
    assert parent_event_in_db.to_primitive() == event_json["result"][1]
    assert event_in_db.to_primitive() == event_json["result"][2]


async def test_get_events_with_update_timestamp_queries(parent_event_in_db,
                                                        event_in_db,
                                                        cli):
    now = datetime.utcnow()
    frm = (now - timedelta(seconds=3)).isoformat()
    to = (now - timedelta(seconds=1)).isoformat()
    resp = await cli.get('/api/v1/event/?frm={0}&to={1}&use_update_time=true'.format(frm, to))
    event_json = (await resp.json())
    assert event_json["count"] == 0

    to = (now + timedelta(seconds=1)).isoformat()
    resp = await cli.get('/api/v1/event/?frm={0}&to={1}'.format(frm, to))
    event_json = (await resp.json())
    assert event_json["count"] == 3
    assert parent_event_in_db.to_primitive() == event_json["result"][1]
    assert event_in_db.to_primitive() == event_json["result"][2]


@pytest.mark.parametrize("frm, to, res",
     [(None, None, 400),
      ('','', 400),
      ('invalid frm time', 'invalid to time', 400)]
)
async def test_get_events_with_invalid_timestamp_queries(frm, to, res,
                                                         cli):
    resp = await cli.get('/api/v1/event/?frm={0}&to={1}'.format(frm, to))
    assert resp.status == res


async def test_get_events_with_timestamp_tag_count(source_event_in_db,
                                                   child_event_of_source_in_db,
                                                   parent_event_in_db,
                                                   event_in_db,
                                                   cli):
    frm = parent_event_in_db.start_time.isoformat()
    to = (event_in_db.start_time + timedelta(hours=1)).isoformat()
    resp = await cli.get('/api/v1/event/?frm={0}'
                                       '&to={1}&tag=environment:'
                                       'monitor_candidate&'
                                       'tag=services:tycho&'
                                       'count=1'.format(frm, to))
    event_json = (await resp.json())
    assert event_json["count"] == 1
    assert event_json["result"][0] == source_event_in_db.to_primitive()
    assert event_in_db.to_primitive() not in event_json["result"]
    assert parent_event_in_db.to_primitive() not in event_json["result"]
    assert child_event_of_source_in_db.to_primitive() \
        not in event_json["result"]


async def test_get_trace_until_source(event_in_db,
                                      parent_event_in_db,
                                      source_event_in_db,
                                      cli):
    resp = await cli.get('/api/v1/event/{0}/trace'.format(
        event_in_db["id"]
    ))
    event_json = (await resp.json())
    result = [Event(elem) for elem in event_json]
    ls = [event_in_db, parent_event_in_db, source_event_in_db]
    for i in range(3):
        assert ls[i].to_primitive() == result[i].to_primitive()


async def test_get_trace_for_source(source_event_in_db,
                                    cli):
    resp = await cli.get('/api/v1/event/{0}/trace'.format(
        source_event_in_db["id"]
    ))
    event_json = (await resp.json())
    result = [Event(elem) for elem in event_json]
    assert source_event_in_db.to_primitive() == result[0].to_primitive()


async def test_get_trace_parent_have_two_children(parent_event_in_db,
                                                  source_event_in_db,
                                                  child_event_of_source_in_db,
                                                  cli):
    resp = await cli.get('/api/v1/event/{0}/trace'.format(
        parent_event_in_db["id"]
    ))
    event_json = (await resp.json())
    result = [Event(elem).to_primitive() for elem in event_json]
    assert child_event_of_source_in_db.to_primitive() not in result


async def test_get_event_impact(cli,
                                source_event_in_db,
                                child_event_of_source_in_db,
                                parent_event_in_db,
                                event_in_db):
    resp = await cli.get('/api/v1/event/{0}/impact'.format(
        source_event_in_db.id
    ))
    assert resp.status == 200

    source_node = (await resp.json())
    assert source_node["event"] == \
        source_event_in_db.to_primitive()

    first_source_child = source_node["children"][0]["event"]
    assert first_source_child == \
        child_event_of_source_in_db.to_primitive()

    second_source_child = source_node["children"][1]
    assert second_source_child["event"] == \
        parent_event_in_db.to_primitive()

    leaf = second_source_child["children"][0]["event"]
    assert leaf == event_in_db.to_primitive()

    child_of_leaf = second_source_child["children"][0]["children"]
    assert child_of_leaf == []


async def test_get_event_impact_diagram(cli, event_in_db):
    resp = await cli.get('/event/{0}/'.format(
        event_in_db.id
    ))
    assert resp.status == 200
    assert resp.content_type == 'text/html'


async def test_get_event_impact_diagram_with_invalid_id(cli):
    event_id = 'dummy_id'
    resp = await cli.get('/event/{0}/'.format(event_id))
    assert resp.status == 404
    resp_text = await resp.text()
    assert resp_text == 'Event ID {} is not available in DB'.format(event_id)


async def test_put_event(db, event, cli):
    resp = await cli.put('/api/v1/event/',
                         headers={"content-type": "application/json"},
                         data=json.dumps({"event":
                                          event.to_primitive()}))
    assert resp.status == 200
    retrieved_event_json = (await resp.json())
    retrieved_event = Event(retrieved_event_json)
    resp2 = await cli.get('/api/v1/event/{0}'.format(
        event.id
    ))
    assert resp2.status == 200
    retrieved_event2_json = (await resp2.json())
    retrieved_event2 = Event(retrieved_event2_json)
    assert (retrieved_event.to_primitive() ==
            retrieved_event2.to_primitive())

async def test_put_invalid_event_raises_exception(cli):
    event_json = {'source_id':
                      '{"affected_services":["static-pre-assy"],'
                      '"phase":"begn","commithash":"cbc010a240e6f'
                      'a5c9b57ec3a367cd1a6b3b6","hst":"host","comm'
                      'itter_email":"user@example.com","author":"example@zill'
                      'ow.com","bugnum":"None","action":"begin","env":"hd1'
                      '", "valid":true,"time":"2016-07-12T10:09:21.162647-07'
                      '","host":"host2.localhost","operation":'
                      '"deploy","tsi":"2016-07-12T17:09:21.163289Z","fmt":'
                      '"ae1","event_source":"shipit","affected_env":["hd1"],'
                      '"change_event_id":"714b7d69-22ef-4d7e-85cb-3'
                      '9c7482aff67","event_id":"600246b0485311e6a5e4aa0000a'
                      'bbe5","description":"None","app":"monitor_live.erro'
                      'r-a.tg-event-announcement","hostname":"wfc-zit-j'
                      'ks-011","status":"None","service":"static-pre-assy",'
                      '"concrete_hash":"cbc010a240e6fa5c9b57ec3a'
                      'cf58367cd1a6b3b6","affected_hosts":["host3-'
                      '001.localhost"],"logname":"deploy-user","autho'
                      'r_emails":["user@example.com"]}',
                      'hostname': 'host.localhost'}

    resp = await cli.put('/api/v1/event/',
                                headers={"content-type": "application/json"},
                                data=json.dumps({"event": event_json})
                                )
    assert resp.status == 400


async def test_post_invalid_event_raises_bad_reqeuest(event, cli):
    event_json = {'source_id':
                      '{"affected_services":["static-pre-assy"],'
                      '"phase":"begn","commithash":"cbc010a240e6f'
                      'a5c9b57ec3a367cd1a6b3b6","hst":"host","comm'
                      'itter_email":"user@example.com","author":"example@zill'
                      'ow.com","bugnum":"None","action":"begin","env":"hd1'
                      '", "valid":true,"time":"2016-07-12T10:09:21.162647-07'
                      '","host":"host2.localhost","operation":'
                      '"deploy","tsi":"2016-07-12T17:09:21.163289Z","fmt":'
                      '"ae1","event_source":"shipit","affected_env":["hd1"],'
                      '"change_event_id":"714b7d69-22ef-4d7e-85cb-3'
                      '9c7482aff67","event_id":"600246b0485311e6a5e4aa0000a'
                      'bbe5","description":"None","app":"monitor_live.erro'
                      'r-a.tg-event-announcement","hostname":"wfc-zit-j'
                      'ks-011","status":"None","service":"static-pre-assy",'
                      '"concrete_hash":"cbc010a240e6fa5c9b57ec3a'
                      'cf58367cd1a6b3b6","affected_hosts":["host3-'
                      '001.localhost"],"logname":"deploy-user","autho'
                      'r_emails":["user@example.com"]}',
                  'hostname': 'host.localhost'}
    resp = await cli.post('/api/v1/event/',
                                headers={"content-type": "application/json"},
                                data=json.dumps({"operation": "merge",
                                                 "event": event_json})
                                )
    assert resp.status == 400


async def test_put_invalid_event_raises_exception_with_to_native(cli):
    with patch("event_tracking.models.event.Event.to_native", return_value = None) as mock_to_native:
        resp = await cli.put('/api/v1/event/',
                                headers={"content-type": "application/json"},
                                data=json.dumps({"event": {}})
                                )
        assert mock_to_native.called
        assert resp.status == 400


async def test_post_invalid_event_raises_bad_reqeuest_with_to_native(event, cli):
    with patch("event_tracking.models.event.Event.to_native", return_value = None) as mock_to_native:
        resp = await cli.post('/api/v1/event/',
                                headers={"content-type": "application/json"},
                                data=json.dumps({"operation": "merge",
                                                 "event": {}})
                                )
        assert mock_to_native.called
        assert resp.status == 400


async def test_post_dont_allow_invalid_opers(event, cli):
    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                            data=json.dumps({"operation":
                                                 "not_merge_nor_update",
                                                 "event":
                                                 event.to_primitive()}))
    assert resp.status == 400


async def test_post_event_merge(event, cli):
    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                            data=json.dumps({"operation":
                                                  "merge",
                                                  "event":
                                                  event.to_primitive()}))
    retrieved_event_json = (await resp.json())
    retrieved_event = Event(retrieved_event_json)
    assert (retrieved_event.to_primitive() ==
            event.to_primitive())
    assert resp.status == 200


async def test_post_event_without_id(event, cli):
    new_event = Event(
        {"description": "Event without id",
         "tags": {"author": ["orbital@example.com"]}
    })
    assert new_event.id != None

    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                            data=json.dumps({"operation":
                                                  "merge",
                                                  "event":
                                                  new_event.to_primitive()}))
    assert resp.status == 200


@pytest.mark.parametrize("upsert", [(True), (False)])
async def test_post_existing_event_with_upsert_option(upsert, event_in_db, cli):
    expected_author = event_in_db.tags["author"]
    new_event = {"id": event_in_db.id,
         "start_time": str(event_in_db.start_time - timedelta(seconds=50)),
         "tags": {"author": ["orbital@example.com"]}
    }
    expected_author.extend(["orbital@example.com"])

    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                            data=json.dumps({"operation":
                                                  "merge",
                                                  "event":
                                                  new_event,
                                                  "insert":
                                                  upsert}))
    assert resp.status == 200

    merged_event_json = (await resp.json())
    merged_event = Event(merged_event_json)
    assert set(expected_author) == set(merged_event.tags["author"])
    delta = event_in_db.start_time - merged_event.start_time
    assert delta.total_seconds() == 50


async def test_post_new_event_with_upsert_option_true(app, event, cli):
    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                                 data=json.dumps({
                                     "operation": "merge",
                                     "event": event.to_primitive(),
                                     "insert": True
                                  }))
    assert resp.status == 200
    merged_event_json = (await resp.json())
    merged_event = Event(merged_event_json)

    result = await app["db"].event.find_by_id(event["id"])
    assert result.to_primitive() == event.to_primitive()


async def test_post_new_event_with_upsert_option_false(app, event, cli):
    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                                 data=json.dumps({
                                     "operation": "merge",
                                     "event": event.to_primitive(),
                                     "insert": False
                                 }))
    assert resp.status == 200
    merged_event_json = (await resp.json())
    merged_event = Event(merged_event_json)

    with pytest.raises(HTTPNotFound):
        await app["db"].event.find_by_id(event["id"])


@pytest.mark.parametrize("new_description, should_merge",
     [(" trigger_deploy ", False),
      ("This is a new trigger_deploy event", True),
      ("", False)])
async def test_merge_description_with_post_existing_event(new_description, should_merge, event_in_db, cli):
    new_event = Event(
        {"id": event_in_db.id,
         "description": new_description
    })

    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                            data=json.dumps({"operation":
                                                  "merge",
                                                  "event":
                                                  new_event.to_primitive(),
                                                  "insert":
                                                  True}))
    assert resp.status == 200
    merged_event_json = (await resp.json())
    merged_event = Event(merged_event_json)
    assert (merged_event.description == event_in_db.description) != should_merge


def test_merge_empty_event_with_new_one():
    existing_event = Event({})
    new_event = Event({"id": existing_event.id,
                       "source_id": "5498d53c5f2d60095267a0bc",
                       "end_time": existing_event.end_time + timedelta(hours=2)})
    _merge(existing_event, new_event)
    assert existing_event.id == new_event.id
    assert existing_event.source_id == new_event.source_id
    assert existing_event.end_time == new_event.end_time
    assert len(existing_event.values()) == len(new_event.values())


def test_update_empty_event_with_new_one():
    existing_event = Event({})
    new_event = Event({"source_id": "5498d53c5f2d60095267a0bc"})
    _update(existing_event, new_event)
    assert existing_event.to_native() == new_event.to_native()


def test_merge_diff_values_of_reserved_keys_raises_exception():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb"})
    new_event = Event({"id": existing_event.id, "source_id": "5498d53c5f2d60095267a0bc"})
    with pytest.raises(ValueError):
        _merge(existing_event, new_event)


def test_merge_two_start_times():
    time = datetime.now()
    existing_event = Event({"start_time": time})
    new_event = Event({"id": existing_event.id, "start_time": time - timedelta(hours=2)})
    _merge(existing_event, new_event)
    assert existing_event["start_time"] == new_event["start_time"]


def test_merge_two_end_times():
    time = datetime.now()
    existing_event = Event({"end_time": time})
    new_event = Event({"id": existing_event.id, "end_time": time + timedelta(hours=2)})
    _merge(existing_event, new_event)
    assert existing_event["end_time"] == new_event["end_time"]


def test_merge_detail_urls():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                            "detail_urls":
                                {"graphite": "http://graphite",
                                 "concrete": "http://concrete"}})

    new_event = Event({"id": existing_event.id,
                       "detail_urls": {"graphite": "http://graphite",
                                       "concrete": "http://concrete"}})
    _merge(existing_event, new_event)
    ls = {"graphite": "http://graphite",
          "concrete": "http://concrete"}
    assert existing_event["detail_urls"] == ls


def test_merge_with_already_existing_keys():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                            "tags": {"author": ["Sean"]}})
    new_event = Event({"id": existing_event.id,
                       "source_id": "5498d53c5f2d60095267a0bb",
                       "tags": {"author": ["Fred"]}})
    _merge(existing_event, new_event)
    assert existing_event.tags["author"] == ["Sean", "Fred"]


def test_merge_two_descriptions():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                           "description":
                           "This is a Concrete Event."})
    new_event = Event({"id": existing_event.id,
                       "description": "The version is 2.2.3."})
    _merge(existing_event, new_event)
    test_str = "This is a Concrete Event.\nThe version is 2.2.3."
    assert existing_event["description"] == test_str


async def test_post_event_update(event, cli):
    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                            data=json.dumps({"operation":
                                                 "update",
                                                 "event":
                                                 event.to_primitive()}))
    retrieved_event_json = (await resp.json())
    retrieved_event = Event(retrieved_event_json)
    assert (retrieved_event.to_primitive() ==
            event.to_primitive())
    assert resp.status == 200

async def test_post_existing_event_update(event_in_db, cli):
    updated_time = event_in_db.start_time - timedelta(seconds=50)
    new_event = {"id": event_in_db.id,
         "start_time": str(updated_time),
         "tags": {"author": ["orbital@example.com"]}
    }
    resp = await cli.post('/api/v1/event/',
                            headers={"content-type": "application/json"},
                            data=json.dumps({"operation":
                                                 "update",
                                                 "event":
                                                 new_event}))
    assert resp.status == 200
    retrieved_event_json = (await resp.json())
    retrieved_event = Event(retrieved_event_json)
    assert event_in_db.id == retrieved_event.id
    assert set(["orbital@example.com"]) == set(retrieved_event.tags["author"])
    assert retrieved_event.start_time == updated_time


async def test_delete_non_existing_event(cli):
    event_id = "event_not_exist"
    resp = await cli.delete("/api/v1/event/{0}/delete".format(event_id))
    assert resp.status == 400
    retrieved_event_json = (await resp.json())
    assert "Can not delete event with id: {0}".format(event_id) in retrieved_event_json["result"]


async def test_delete_existing_event(cli, event_in_db):
    resp = await cli.delete("/api/v1/event/{0}/delete".format(event_in_db.id))
    assert resp.status == 200
    retrieved_event_json = (await resp.json())
    assert "Event: {0} deleted successfully".format(event_in_db.id) == retrieved_event_json["message"]
    resp = await cli.get('/api/v1/event/{0}'.format(
        event_in_db.id
    ))
    assert 404 == resp.status


def test_non_string_description_raises_exception():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                           "description":
                           "This is a Concrete Event."})
    with pytest.raises(DataError):
        new_event = Event({"id": existing_event.id,
                           "description": [1234]})
        _merge(existing_event, new_event)


def test_same_values_not_added_twice():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                            "tags": {"author": ["Fred"]}})
    new_event = Event({"id": existing_event.id,
                       "tags": {"author": ["Fred"]}})
    _merge(existing_event, new_event)
    assert existing_event.tags["author"] == ["Fred"]


def test_merge_two_attrs_of_type_lists_with_duplicates():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                            "tags": {"author": ["Fred", "Sean"]}})
    new_event = Event({"id": existing_event.id,
                       "tags": {"author": ["Fred", "Mayur"]}})
    _merge(existing_event, new_event)
    assert existing_event.tags["author"] == ["Fred", "Sean", "Mayur"]


def test_merge_new_attributes():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                            "tags": {"author": ["Tom"]}})
    new_event = Event({"id": existing_event.id,
                       "tags": {"reviewer": ["Fred"]}})
    _merge(existing_event, new_event)
    assert existing_event.tags["reviewer"] == ["Fred"]


def test_update_non_existing_values():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb"})
    new_event = Event({"parent_id": "5498d53c5f2d60095267a0bb"})
    _update(existing_event, new_event)
    assert existing_event["parent_id"] == "5498d53c5f2d60095267a0bb"


def test_update_existing_values():
    existing_event = Event({"source_id": "5498d53c5f2d60095267a0bb",
                            "tags": {"author": ["Tom"]}})
    new_event = Event({"tags": {"author": ["Fred"]}})
    _update(existing_event, new_event)
    assert existing_event.tags["author"] == ["Fred"]


async def test_user_route(cli):
    resp = await cli.get('/')
    assert 200 == resp.status
    text = await resp.text()
    assert "html" in text
