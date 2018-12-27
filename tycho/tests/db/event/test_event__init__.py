import pytest
import attr
from aiohttp.web import HTTPNotFound
from datetime import datetime, timedelta
from tycho.models.event import Event
from copy import deepcopy
from tycho.db.event import MAX_RECURSIVE_DEPTH


async def test_save_data(app, event):
    await app["db"].event.save(event)
    result = await app["db"].event.find_one()
    assert attr.asdict(result) == attr.asdict(event)


async def test_find_one_data_exists(app, event):
    await app["db"].event.save(event)
    result = await app["db"].event.find_one()
    assert result == event


async def test_find_one_data_not_exists(app):
    result = await app["db"].event.find_one()
    assert result == Event(**{"id": result.id,
                              "start_time": result.start_time,
                              "end_time": result.end_time})


async def test_find_by_id_data_exist(app, event):
    await app["db"].event.save(event)
    result = await app["db"].event.find_by_id(event.id)
    assert result == event


async def test_find_by_id_when_no_event_present(app, event):
    with pytest.raises(HTTPNotFound):
        result = await app["db"].event.find_by_id(123)


async def test_trace_stops_at_nonexistent_parent(app, event):
    """
    trace should stop at the first missing parent, rather
    than raise an exception.
    """
    await app["db"].event.save(event)
    result = await app["db"].event.trace(event.id)
    assert len(result) == 1


async def test_event_trace_with_empty_parent_id(app, event):
    event_copy = deepcopy(event)
    event_copy.parent_id = "dummy_parent_id"

    child_event_copy = deepcopy(event_copy)
    child_event_copy.id = "dummy_parent_id"
    child_event_copy.parent_id = ""
    await app["db"].event.save(event_copy)
    await app["db"].event.save(child_event_copy)

    result = await app["db"].event.trace(event_copy.id)
    assert len(result) == 2
    assert result[0].id == event_copy.id
    assert result[1].id == child_event_copy.id


async def test_event_trace_with_max_recursive_depth(app, event):
    i = 0
    curr_id = event.id
    parent_id = curr_id + str(i)
    event_copy = deepcopy(event)
    while i < MAX_RECURSIVE_DEPTH + 10:
        event_copy.id = curr_id
        event_copy.parent_id = parent_id
        await app["db"].event.save(event_copy)
        i += 1
        curr_id = parent_id
        parent_id = event.id + str(i)

    result = await app["db"].event.trace(event.id)
    assert len(result) == MAX_RECURSIVE_DEPTH


async def test_update_by_id(app, event):
    await app["db"].event.save(event)
    prev_event = await app["db"].event.find_by_id(event.id)
    assert prev_event.tags["status"] == ["success"]
    prev_event.tags["status"] = ["Fail"]
    await app["db"].event.update_by_id(event.id, prev_event)
    result = await app["db"].event.find_by_id(event.id)
    assert result.tags["status"] == ["Fail"]


async def test_update_by_id_on_nothing(app, event):
    await app["db"].event.update_by_id(event.id, event)
    with pytest.raises(HTTPNotFound):
        result = await app["db"].event.find_by_id(event.id)


async def test_find_by_parent_id(app, event):
    await app["db"].event.save(event)
    id = event.parent_id
    result = []
    async for doc in await app["db"].event.find_by_parent_id(id):
        result.append(doc)
    assert attr.asdict(event) == attr.asdict(result[0])


async def test_find_by_env_and_service(app, source_event_in_db):
    env = source_event_in_db.tags["environment"][0]
    service = source_event_in_db.tags["services"][0]
    tags = ['environment:{0}'.format(env),
            'services:{0}'.format(service)]
    result = []
    docs = await app["db"].event.find(tags=tags)
    async for doc in docs:
        result.append(doc)
    assert attr.asdict(result[0]) == attr.asdict(source_event_in_db)


async def test_find_by_env_and_service_no_event_returns_empty_list(
        app, event_in_db):
    tags = ['environment:val_300',
            'services:{0}'.format(
                event_in_db.tags["services"][0])]
    result = []
    docs = await app["db"].event.find(tags=tags)
    async for doc in docs:
        result.append(doc)
    assert result == []


async def test_get_most_recent_events(app, source_event_in_db,
                                      child_event_of_source_in_db,
                                      parent_event_in_db,
                                      event_in_db
                                      ):
    docs = await app["db"].event.find(count=4)
    result = []
    async for doc in docs:
        result.append(doc)
    event_list = [
        child_event_of_source_in_db,
        source_event_in_db,
        parent_event_in_db,
        event_in_db
    ]
    for i in range(len(event_list)):
        assert attr.asdict(event_list[i]) == attr.asdict(result[i])


async def test_get_recent_events_count_equals_one(app, source_event_in_db,
                                                  child_event_of_source_in_db,
                                                  parent_event_in_db,
                                                  event_in_db
                                                  ):
    docs = await app["db"].event.find(count=1)
    result = []
    async for doc in docs:
        result.append(doc)
    event_list = [
                  child_event_of_source_in_db,
                  source_event_in_db,
                  parent_event_in_db,
                  event_in_db
                  ]
    assert result[0].to_primitive() == event_list[0].to_primitive()
    assert len(result) == 1


async def test_get_recent_events_count_equals_zero(app, source_event_in_db,
                                                   child_event_of_source_in_db,
                                                   parent_event_in_db,
                                                   event_in_db
                                                   ):
    """ if the count parameter is 0, the result should be unbounded
    and return all documents.
    """
    docs = await app["db"].event.find(count=0)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 4


async def test_get_events_by_count_and_page(app, source_event_in_db,
                                            child_event_of_source_in_db,
                                            parent_event_in_db,
                                            event_in_db
                                            ):
    event_list = [
                  child_event_of_source_in_db,
                  source_event_in_db,
                  parent_event_in_db,
                  event_in_db
                  ]
    # first test
    docs = await app["db"].event.find(count=1, page=1)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 1
    assert attr.asdict(result[0]) == attr.asdict(event_list[0])

    # second test of the same sorts
    second_docs = await app["db"].event.find(count=2, page=2)
    result = []
    async for doc in second_docs:
        result.append(doc)
    assert len(result) == 2
    assert attr.asdict(result[0]) == attr.asdict(event_list[2])
    assert attr.asdict(result[1]) == attr.asdict(event_list[3])


async def test_page_count_less_than_one_raises_exception(app,
                                                         event_in_db):
    with pytest.raises(ValueError):
        await app["db"].event.find(count=1, page=0)


async def test_get_event_neg_count_raise_exception(app, event_in_db,
                                                   parent_event_in_db,
                                                   child_event_of_source_in_db,
                                                   source_event_in_db,
                                                   ):
    with pytest.raises(ValueError):
        await app["db"].event.find(count=-1)


async def test_get_events_by_timestamp(app, source_event_in_db, parent_event_in_db, event_in_db):
    to = source_event_in_db.start_time
    frm = event_in_db.start_time
    docs = await app["db"].event.find(frm=frm, to=to)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 2
    assert parent_event_in_db.to_primitive() == result[0].to_primitive()
    assert event_in_db.to_primitive() == result[1].to_primitive()

    to = source_event_in_db.end_time + timedelta(seconds=1)
    docs = await app["db"].event.find(frm=frm, to=to)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 3
    assert source_event_in_db.to_primitive() == result[0].to_primitive()
    assert parent_event_in_db.to_primitive() == result[1].to_primitive()
    assert event_in_db.to_primitive() == result[2].to_primitive()


async def test_get_events_by_update_timestamp(app, source_event_in_db, update_event_in_db,
                                              update_time, patch_update_time):
    frm = update_time - timedelta(seconds=10)
    to = update_time - timedelta(seconds=5)

    docs = await app["db"].event.find(frm=frm, to=to, use_update_time=True)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 0

    to = update_time + timedelta(seconds=1)
    docs = await app["db"].event.find(frm=frm, to=to, use_update_time=True)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 2
    expected_results = [
        source_event_in_db.to_primitive(),
        update_event_in_db.to_primitive(),
    ]
    assert result[0].to_primitive() in expected_results
    assert result[1].to_primitive() in expected_results

    # search with start/end time should not return update_event
    docs = await app["db"].event.find(frm=frm, to=to, use_update_time=False)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 0


async def test_get_events_with_only_one_timestamp(app, source_event_in_db,
                                                  parent_event_in_db,
                                                  event_in_db
                                                  ):
    to = source_event_in_db.start_time
    docs = await app["db"].event.find(to=to)
    result = []
    async for doc in docs:
        result.append(doc)
    # results will include up to, but not including, source event.
    assert len(result) == 2
    assert parent_event_in_db.to_primitive() == result[0].to_primitive()
    assert event_in_db.to_primitive() == result[1].to_primitive()

    to = source_event_in_db.start_time + timedelta(seconds=1)
    docs = await app["db"].event.find(to=to)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 3
    assert source_event_in_db.to_primitive() == result[0].to_primitive()
    assert parent_event_in_db.to_primitive() == result[1].to_primitive()
    assert event_in_db.to_primitive() == result[2].to_primitive()


async def test_get_tree(app, source_event_in_db,
                        child_event_of_source_in_db,
                        parent_event_in_db,
                        event_in_db):
    source_node = await app["db"].event.get_tree(
        source_event_in_db.id)
    assert source_node.event.to_primitive() == \
        source_event_in_db.to_primitive()

    first_source_child = source_node.children[0].event
    assert first_source_child.to_primitive() == \
        child_event_of_source_in_db.to_primitive()

    second_source_child = source_node.children[1]
    assert second_source_child.event.to_primitive() == \
        parent_event_in_db.to_primitive()

    leaf = second_source_child.children[0].event
    assert leaf.to_primitive() == event_in_db.to_primitive()

    child_of_leaf = second_source_child.children[0].children
    assert child_of_leaf == []


async def test_bfs_traversal_on_leaf(app, event_in_db):
    leaf_node = await app["db"].event.get_tree(
        event_in_db.id
    )
    assert leaf_node.event.id == event_in_db.id
    assert leaf_node.children == []


async def test_delete_event(app, event_in_db):
    result = await app["db"].event.delete_by_id(event_in_db.id)
    assert True == result


async def test_delete_invalid_event(app):
    result = await app["db"].event.delete_by_id("event_not_exist")
    assert False == result
