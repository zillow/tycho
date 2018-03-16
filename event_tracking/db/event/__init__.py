import pymongo
from ..utils import async_generator
from ...models.eventnode import EventNode
from ...models.event import Event as ModelEvent
from aiohttp_transmute import APIException
from aiohttp.web import HTTPNotFound
import queue as q

from .deserialize import deserialize_db_event
from .serialize import serialize_to_db_event


class Event:
    _collection = 'event'

    indexes = [
        {'unique': False, 'keys': [("tags", pymongo.ASCENDING)]},
        {'unique': False, 'keys': [("time", pymongo.ASCENDING)]},
        {'unique': False, 'keys': [("update_time", pymongo.ASCENDING)]}
    ]

    def __init__(self, collection):
        self.collection = collection

    async def save(self, data: ModelEvent):
        new_db_format = serialize_to_db_event(data)
        result = await self.collection.save(new_db_format)
        return result

    async def find_one(self) -> ModelEvent:
        result = await self.collection.find_one()
        return deserialize_db_event(result)

    async def find_by_id(self, id) -> ModelEvent:
        document = None
        cursor = self.collection.find({"_id": id})
        while(await cursor.fetch_next):
            document = cursor.next_object()
        if document is None:
            raise HTTPNotFound(text="cannot find event {0}".format(id))
        return deserialize_db_event(document)

    async def update_by_id(self, id, update_doc: ModelEvent, insert: bool=False):
        new_data = serialize_to_db_event(update_doc)
        result = await self.collection.update(
            {"_id": id}, new_data, upsert=insert)
        return result

    async def find_by_parent_id(self, id):
        cursor = self.collection.find({"tags":
                                       {"$in": ["parent_id:{0}".format(id)]}})
        return async_generator(cursor, deserialize_db_event)

    async def find(self, tags=None, frm=None, to=None, use_update_time=False,
                   count=100, page=1):
        if count < 0:
            raise ValueError("Count must be greater than or equal to zero.")

        if page < 1:
            raise ValueError(
                "Page count must be greater than or equal to one.")

        time_field = "update_time" if use_update_time else "time"

        query = {}
        if tags is not None:
            query["tags"] = {"$all": tags}
        if frm is not None:
            query[time_field] = {"$gte": frm}
        if to is not None:
            if query.get(time_field) is None:
                query[time_field] = {"$lt": to}
            else:
                query[time_field]["$lt"] = to
        cursor = self.collection.find(query).sort([(time_field, -1)]).skip(
            (page-1)*count).limit(count)
        return async_generator(cursor, deserialize_db_event)

    async def get_tree(self, id):
        root_event = await self.find_by_id(id)
        root_event_node = EventNode({"event": root_event})
        queue = q.Queue()
        queue.put(root_event_node)
        while (not queue.empty()):
            event_node = queue.get()
            children = await self.find_by_parent_id(event_node.event.id)
            async for child in children:
                child_node = EventNode({"event": child})
                if child_node not in event_node.children:
                    event_node.children.append(child_node)
                queue.put(child_node)
        return root_event_node

    async def trace(self, event_id):
        """ return back the root-level parent id of the event """
        result = []
        currId = event_id
        while (currId is not None):
            try:
                doc = await self.find_by_id(currId)
                result.append(doc)
                currId = doc.get("parent_id")
            except HTTPNotFound:
                currId = None
        return result

    async def delete_by_id(self, id) -> bool:
        """ deletes event with provided id and returns True otherwise False"""
        result_map = {0: False, 1: True, None: False}
        result = await self.collection.remove({"_id": id})
        return result_map[result.get('n', None)]
