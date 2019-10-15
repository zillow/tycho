import aiohttp_transmute
import attr
import json
import os
import logging
from aiohttp import web
from aiohttp.web import HTTPNotFound
from aiohttp_transmute import (APIException, add_route, route)
from datetime import datetime
from ..models.eventnode import EventNode
from ..models.events_with_count import EventListWithCount
from ..models.event import Event

from ..templates import get_template


LOG = logging.getLogger(__name__)


@aiohttp_transmute.describe(methods="GET", paths="/api/v1/event/{event_id}")
async def get_event(request, event_id: str) -> Event:
    """
    returns the event stored in the db given its id
    :param request: the request object
    :param event_id: the unique id corresponding to the event
    :return: Event object
    """
    event = await request.app["db"].event.find_by_id(event_id)
    return event


@aiohttp_transmute.describe(methods="GET",
                            paths="/api/v1/event/{event_id}/children")
async def get_children_events(request, event_id: str) -> [Event]:
    """
     returns a event's children events given the parent's event id
     :param request: the request object
     :param event_id: the unique id corresponding to the parent event
     :return: parent event's children as a list
    """
    result = []
    async for doc in await request.app["db"].event.find_by_parent_id(event_id):
        result.append(doc)
    return result


@aiohttp_transmute.describe(methods="GET",
                            paths="/api/v1/event/{event_id}/trace")
async def get_parent_events_until_source(request, event_id: str) -> [Event]:
    """
     returns the whole branch of events up until the source
     given the child's event id
     :param request: the request object
     :param event_id: the unique id corresponding to the child event
     :return: list of parents until the source as a list
    """
    return (await request.app["db"].event.trace(event_id))


@aiohttp_transmute.describe(methods="GET",
                            paths="/api/v1/event/")
async def get_events(request, count: int = 100,
                     frm: datetime = None, to: datetime = None,
                     use_update_time: bool = False,
                     tag: [str] = None, page: int = 1) -> EventListWithCount:
    """
    return events based on query parameters
    :param request: the client request object

    :param count: the number of events to be returned, default=100

    :param frm: if provided, the events returned will be the ones
            with start_time on and after this timestamp, default=None

    :param to: if provided, the events returned will be the ones
            with start_time before this timestamp, default=None

    :param: use_update_time: search by ets event update time or
             event provided start and end times, default=False

    :param page: the attribute for pagination of events,
               default=1

    :param tag: the list of other query parameters, including
         environment, services and description, default=None

    :return: The 'EventListwithCount' object, which has the list
             of events to be returned in its 'result' field,
             and the number of results in its 'count' field
    """
    result = []
    qry = {"tags": tag, "count": count, "page": page,
           "use_update_time": use_update_time}

    for param in ['frm', 'to']:
        value = eval(param)
        if value:
            qry.update({param: value})

    docs = await request.app["db"].event.find(**qry)
    async for doc in docs:
        result.append(doc)
    count = len(result)
    event_with_count = EventListWithCount(result=result, count=count)
    return event_with_count


@aiohttp_transmute.describe(methods="GET",
                            paths="/api/v1/event/{event_id}/impact")
async def get_event_impact(request, event_id: str) -> EventNode:
    """
    gets the whole impact of an event given its id.
    Eg:

    ```
    1
    | \\
    2  3
    | \\
    4  5
    ```

    Given '1's id, this function would return the node
    representation of the above tree with pointer to the root.

    :param request: the object representing the client request
    :param event_id: the id corresponding to the source
    :return: the impact of the source node.
    """
    event = await request.app["db"].event.get_tree(event_id)
    return event


@aiohttp_transmute.describe(methods="PUT", paths="/api/v1/event/")
async def put_event(request, event: Event) -> Event:
    """
    stores a new event on the database
    :param request: the object representing the client request
    :param event: the event to be stored
    :return: the stored event
    """
    await request.app["db"].event.save(event)
    if request.app["config"].log_events:
        LOG.info(event.to_primitive())
    return event


@aiohttp_transmute.describe(methods="DELETE", paths="/api/v1/event/{event_id}/delete")
async def delete_event(request, event_id: str) -> bool:
    """
        deletes an existing event with event_id
        :param request: the request object
        :param event_id: the id corresponding to the source
        :return: the result of delete operation (msg)
    """
    result = await request.app["db"].event.delete_by_id(event_id)
    if not result:
        raise APIException(
            "Can not delete event with id: {0}".format(event_id))
    return {'message': 'Event: {0} deleted successfully'.format(event_id)}


@aiohttp_transmute.describe(methods="POST", paths="/api/v1/event/")
async def post_event(request, event: Event,
                     operation: str = "merge", insert: bool = False) -> Event:
    """
        merge or update an existing event with a new one
        :param request: the request object
        :param operation: takes either "merge" or "update":
           - merge will merge the existing event with the new event and
             raise an exception whenever merge isn't possible
           - update will update the values in the existing event with
             the new values given by the post request and add new values
        :return: the updated/merged event
    """
    if operation != "merge" and operation != "update":
        raise APIException(
            "only update and merge operation are supported, {0} passed".format(operation))

    try:
        existing_event = await request.app["db"].event.find_by_id(event.id)
        if operation == "merge":
            _merge(existing_event, event)
        else:
            _update(existing_event, event)
    except HTTPNotFound:
        existing_event = event

    if request.app["config"].log_events:
        LOG.info(event.to_primitive())
    await request.app["db"].event.update_by_id(event.id, existing_event, insert)
    return existing_event


def _merge(existing_event, new_event):
    """
    A helper function to merge the existing event with the
    new values given by the new_eventionary

    :param: existing_event: The event that's already in the database
    :param: the dictionary with new attributes to merge with the existing event
    :modifies: existing_event with the merged values
    """
    new_event_dict = attr.asdict(new_event)
    for key in new_event_dict:
        if new_event_dict.get(key):
            # try merging the values which share the same keys
            if getattr(existing_event, key):
                if key != "tags":
                    _merge_reserved_keys(key, existing_event, new_event)
                else:
                    # merge the values so that the resulting value is a dict
                    _add_to_dict(key, existing_event, new_event)
            # else just add the new values to our event
            else:
                setattr(existing_event, key, new_event_dict[key])


def _merge_reserved_keys(key, existing_event, new_event):
    """
    A helper function that merges the reserved keys or raises an exception
    when merge not possible
    :param key: The key to be merged
    :param existing_event: The event that's already in the database
    :param new_event: the new event to be merged
    :return: the dictionary with new attributes to merge with
             the existing event
    """
    # change the start time to be the earlier
    # of the two keys
    if key == "start_time":
        if new_event.start_time is not None:
            existing_event.start_time = min(
                new_event.start_time, existing_event.start_time)

    elif key == "end_time":
        # change the end time to be the later
        # of the two keys
        if new_event.end_time is not None:
            existing_event.end_time = max(
                new_event.end_time, existing_event.end_time)

    elif key == "description":
        # append the new_event's description to the already existing one
        str1 = existing_event.description.strip()
        str2 = new_event.description.strip()
        if str2 and str2 not in str1:
            # Adding new line as a separator of events description
            existing_event.description = str1 + "\n" + str2

    elif key == "detail_urls":
        # merge two detail_urls lists given by new_event and existing_event
        for k in new_event.detail_urls:
            if new_event.detail_urls.get(k) is not None:
                existing_event.detail_urls[k] = new_event.detail_urls[k]
    else:
        # raise exception if the other reserved vals don't match
        if getattr(existing_event, key) != getattr(new_event, key):
            raise ValueError("Merge not possible:"
                             "reserved keys have clashing values.")


def _add_to_dict(key, existing_event, new_event):
    """
    A helper function that merges the keys whose values is a list
    :param key: the key corresponding to the values to be added
    :param existing_event: the already existing event in the db
    :param new_event: the new db to be merged
    :modifies the existing_event with the merged values
    """
    prev = getattr(existing_event, key)
    new = getattr(new_event, key)

    for k in new:
        if k not in prev:
            prev[k] = new[k]
        else:
            for elem in new[k]:
                if elem not in prev[k]:
                    prev[k].append(elem)

    setattr(existing_event, key, prev)


def _update(existing_event, new_event):
    """
    A helper function which updates the existing event in the database
    to new values given by the data in put request

    :param: existing_event: The event that's already in the database
    :param: the dictionary with new attributes to merge with the existing event
    :modifies: existing_event with the merged values

    """
    new_event_dict = attr.asdict(new_event)

    for key in new_event_dict:
        if new_event_dict.get(key) is not None:
            setattr(existing_event, key, new_event_dict[key])


async def get_event_root_and_impact_diagram(request):
    """
    traverses the given event_id to the root, then finds the impact
    of that event.
    """
    event_id = request.match_info['event_id']
    event_tree = (await request.app["db"].event.trace(event_id))
    if not event_tree:
        raise HTTPNotFound(
            text='Event ID {} is not available in DB'.format(event_id))
    root_event = event_tree[-1]
    event = await request.app["db"].event.get_tree(root_event.id)

    body = get_template("diagrams.html").render(
        config=request.app["config"], rawData=json.dumps(event.to_primitive())
    ).encode("UTF-8")

    return web.Response(body=body, content_type="text/html")


def add_statics(app):
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    STATIC_ROOT = os.path.join(APP_ROOT, "tycho", "static")
    app.router.add_static('/static', STATIC_ROOT)


def add_event_api(app):
    route(app, get_event)
    route(app, post_event)
    route(app, delete_event)
    route(app, put_event)
    route(app, get_children_events)
    route(app, get_parent_events_until_source)
    route(app, get_events)
    route(app, get_event_impact)
    app.router.add_route(
        'GET', "/event/{event_id}/", get_event_root_and_impact_diagram)
