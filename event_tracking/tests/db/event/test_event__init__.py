import pytest
from aiohttp.web import HTTPNotFound
from datetime import datetime, timedelta
from event_tracking.models.event import Event


async def test_save_data(app, event):
    await app["db"].event.save(event)
    result = await app["db"].event.find_one()
    assert result.to_native() == event.to_native()


async def test_find_one_data_exists(app, event):
    await app["db"].event.save(event)
    result = await app["db"].event.find_one()
    assert result == event


async def test_find_one_data_not_exists(app):
    result = await app["db"].event.find_one()
    assert result == Event({"id": result.id,
                            "start_time": result.start_time,
                            "end_time": result.end_time})


async def test_find_by_id_data_exist(app, event):
    await app["db"].event.save(event)
    id = event["id"]
    result = await app["db"].event.find_by_id(id)
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
    result = await app["db"].event.trace(event["id"])
    assert len(result) == 1


async def test_update_by_id(app, event):
    await app["db"].event.save(event)
    id = event["id"]
    prev_event = await app["db"].event.find_by_id(id)
    assert prev_event["tags"]["status"] == ["success"]
    prev_event["tags"]["status"] = ["Fail"]
    await app["db"].event.update_by_id(id, prev_event)
    result = await app["db"].event.find_by_id(id)
    assert result["tags"]["status"] == ["Fail"]


async def test_update_by_id_on_nothing(app, event):
    id = event["id"]
    await app["db"].event.update_by_id(id, event)
    with pytest.raises(HTTPNotFound):
        result = await app["db"].event.find_by_id(id)


async def test_find_by_parent_id(app, event):
    await app["db"].event.save(event)
    id = event["parent_id"]
    result = []
    async for doc in await app["db"].event.find_by_parent_id(id):
        result.append(doc)
    assert event.to_native() == result[0].to_native()


async def test_find_by_env_and_service(app, source_event_in_db):
    env = source_event_in_db.tags["environment"][0]
    service = source_event_in_db.tags["services"][0]
    tags = ['environment:{0}'.format(env),
            'services:{0}'.format(service)]
    result = []
    docs = await app["db"].event.find(tags=tags)
    async for doc in docs:
        result.append(doc)
    assert result[0].to_primitive() == source_event_in_db.to_primitive()


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
    event_list = [source_event_in_db,
                  child_event_of_source_in_db,
                  parent_event_in_db,
                  event_in_db
                  ]
    for i in range(len(event_list)):
        assert event_list[i].to_primitive() == result[i].to_primitive()


async def test_get_recent_events_count_equals_one(app, source_event_in_db,
                                                  child_event_of_source_in_db,
                                                  parent_event_in_db,
                                                  event_in_db
                                                  ):
    docs = await app["db"].event.find(count=1)
    result = []
    async for doc in docs:
        result.append(doc)
    event_list = [source_event_in_db,
                  child_event_of_source_in_db,
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
    docs = await app["db"].event.find(count=0)
    result = []
    async for doc in docs:
        result.append(doc)
    event_list = [source_event_in_db,
                  child_event_of_source_in_db,
                  parent_event_in_db,
                  event_in_db
                  ]
    assert len(result) == 4
    for i in range(4):
        assert result[i].to_primitive() == event_list[i].to_primitive()


async def test_get_events_by_count_and_page(app, source_event_in_db,
                                            child_event_of_source_in_db,
                                            parent_event_in_db,
                                            event_in_db
                                            ):
    event_list = [source_event_in_db,
                  child_event_of_source_in_db,
                  parent_event_in_db,
                  event_in_db
                  ]
    # first test
    docs = await app["db"].event.find(count=1, page=1)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 1
    assert result[0].to_primitive() == event_list[0].to_primitive()

    # second test of the same sorts
    second_docs = await app["db"].event.find(count=2, page=2)
    result = []
    async for doc in second_docs:
        result.append(doc)
    assert len(result) == 2
    assert result[0].to_primitive() == event_list[2].to_primitive()
    assert result[1].to_primitive() == event_list[3].to_primitive()


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
    frm = parent_event_in_db.start_time
    to = event_in_db.start_time
    docs = await app["db"].event.find(frm=frm, to=to)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 2
    assert source_event_in_db.to_primitive() == result[0].to_primitive()
    assert parent_event_in_db.to_primitive() == result[1].to_primitive()

    to = event_in_db.start_time + timedelta(seconds=1)
    docs = await app["db"].event.find(frm=frm, to=to)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 3
    assert source_event_in_db.to_primitive() == result[0].to_primitive()
    assert parent_event_in_db.to_primitive() == result[1].to_primitive()
    assert event_in_db.to_primitive() == result[2].to_primitive()


async def test_get_events_by_update_timestamp(app, source_event_in_db, update_event_in_db):
    now = datetime.utcnow()
    frm = now - timedelta(seconds=10)
    to = now - timedelta(seconds=5)

    docs = await app["db"].event.find(frm=frm, to=to, use_update_time=True)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 0

    to = now + timedelta(seconds=1)
    docs = await app["db"].event.find(frm=frm, to=to, use_update_time=True)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 2
    assert update_event_in_db.to_primitive() == result[0].to_primitive()
    assert source_event_in_db.to_primitive() == result[1].to_primitive()

    # search with start/end time should not return update_event
    docs = await app["db"].event.find(frm=frm, to=to, use_update_time=False)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 1
    assert source_event_in_db.to_primitive() == result[0].to_primitive()


async def test_get_events_with_only_one_timestamp(app, source_event_in_db,
                                                  parent_event_in_db,
                                                  event_in_db
                                                  ):
    to = event_in_db.start_time
    docs = await app["db"].event.find(to=to)
    result = []
    async for doc in docs:
        result.append(doc)
    assert len(result) == 2
    assert source_event_in_db.to_primitive() == result[0].to_primitive()
    assert parent_event_in_db.to_primitive() == result[1].to_primitive()

    to = event_in_db.start_time + timedelta(seconds=1)
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
