import datetime
import os
import pytest
import socket
from unittest import mock
from datetime import timedelta
from aiohttp import request
import asyncio
from tycho.app import create_app
from tycho.db import init_db
from tycho.models.config import Config, Mongo
from tycho.models.eventdb import EventDB as ModelEventDB
from tycho.models.event import Event as ModelEvent, CATTRS_CONVERTER
from tycho.routes.event import Event

global_source_id = "222f1f77bcf86cd799439011"
# pytest_plugins = 'aiohttp.pytest_plugin'

DB_NAME = "tycho-tests-{}".format(os.getpid())

DB_CONFIG = Mongo({
    "uri": "mongodb://localhost:27017/?maxPoolSize=10&w=1",
    "db_name": DB_NAME,
})


@pytest.fixture
def event_db():
    return mock.Mock()


@pytest.fixture
def collections():
    return [Event]


@pytest.fixture
def config():
    config_json = Config.get_mock_object().to_primitive()
    config_json["mongo"] = DB_CONFIG.to_primitive()
    config_model = Config(config_json)
    return config_model


@pytest.fixture
def app(loop, config, db):
    return create_app(config, db=db)

@pytest.yield_fixture
def db(loop, config):
    asyncio.set_event_loop(loop)
    _db = init_db(config.mongo)
    yield _db
    if _db:
        loop.run_until_complete(_db.command("dropDatabase"))


@pytest.fixture
def cli(loop, aiohttp_client, config, app):
    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def patch_update_time(update_time, monkeypatch):
    with mock.patch("tycho.db.event.serialize.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = update_time
        yield


@pytest.fixture
def start_time():
    return datetime.datetime.utcnow()


@pytest.fixture
def update_time():
    return datetime.datetime.utcnow()


@pytest.fixture
def end_time(start_time):
    return start_time + timedelta(days=1)


@pytest.fixture
def event(start_time, end_time):
    """
    * should occur before all events.
    """
    global global_source_id
    return ModelEvent(**{
        "id": "5498d53c5f2d60095267a0bb",
        "source_id": global_source_id,
        "parent_id": "111f1f77bcf86cd799439011",
        "start_time": start_time,
        "end_time": end_time,
        "detail_urls": {"jira": "http://jira", "graphite": "http://graphite"},
        "description": "This is a trigger_deploy event.",
        "tags": {
            "source": ["deploy"],
            "type": ["deploy/deploy_all"],
            "author": ["user@example.com"],
            "environment": ["monitor_candidate", "monitor_live"],
            "services": ["tycho"],
            "status": ["success"]
        }
    })


@pytest.fixture
def parent_event(end_time):
    """
    should occur right after event
    """
    global global_source_id
    # parent of the event fixture and child of the source
    return ModelEvent(**{
        "id": "111f1f77bcf86cd799439011",
        "source_id": global_source_id,
        "parent_id": "222f1f77bcf86cd799439011",
        "start_time": end_time + datetime.timedelta(hours=1),
        "end_time": end_time + datetime.timedelta(hours=2),
        "detail_urls": {"jira": "http://jira", "graphite": "http://graphite"},
        "description": "This is a trigger_deploy event.",
        "tags": {
            "source": ["deploy"],
            "type": ["deploy/deploy_all"],
            "author": ["user@example.com"],
            "environment": ["monitor_candidate", "monitor_live"],
            "services": ["tycho"],
            "status": ["success"]
        }
    })


@pytest.fixture
def child_event_of_source(end_time):
    """
    * should come right after source_event.
    """
    global global_source_id
    # second child of the source event
    return ModelEvent(**{
        "id": "333f1f77bcf86cd799439333",
        "source_id": global_source_id,
        "parent_id": global_source_id,
        "start_time": end_time + datetime.timedelta(hours=5),
        "end_time": end_time + datetime.timedelta(hours=6),
        "detail_urls": {"jira": "http://jira", "graphite": "http://graphite"},
        "description": "This is a trigger_deploy event.",
        "tags": {
            "source": ["deploy"],
            "type": ["deploy/deploy_all"],
            "author": ["user@example.com"],
            "environment": ["monitor_candidate", "monitor_live"],
            "services": ["tycho"],
            "status": ["success"]
        }
    })


@pytest.fixture
def source_event(end_time):
    """
    * should come after parent_event
    """
    return ModelEvent(**{
        "id": "222f1f77bcf86cd799439011",
        "start_time": end_time + datetime.timedelta(hours=3),
        "end_time": end_time + datetime.timedelta(hours=4),
        "detail_urls": {"jira": "http://jira", "graphite": "http://graphite"},
        "description": "This is a trigger_deploy event.",
        "tags": {
            "source": ["deploy"],
            "type": ["deploy/deploy_all"],
            "author": ["user@example.com"],
            "environment": ["monitor_candidate", "monitor_live"],
            "services": ["tycho"],
            "status": ["success"]
        }
    })


@pytest.fixture
def update_event(start_time, end_time):
    return ModelEvent(**{
        "id": "578524407e7ac034e407dbd2",
        "start_time": start_time - datetime.timedelta(days=3),
        "end_time": end_time - datetime.timedelta(days=2),
        "detail_urls": {"jira": "http://jira", "graphite": "http://graphite"},
        "description": "This is a trigger_deploy event.",
        "tags": {
            "source": ["deploy"],
            "type": ["deploy/deploy_all"],
            "author": ["user@example.com"],
            "environment": ["monitor_candidate", "monitor_live"],
            "services": ["tycho"],
            "status": ["success"]
        }
    })


@pytest.fixture
def event_in_db(loop, event, db, parent_event_in_db):
    loop.run_until_complete(db.event.save(event))
    return event


@pytest.fixture
def parent_event_in_db(loop, parent_event, db, source_event_in_db):
    loop.run_until_complete(db.event.save(parent_event))
    return parent_event


@pytest.fixture
def source_event_in_db(loop, source_event, db, patch_update_time):
    loop.run_until_complete(db.event.save(source_event))
    return source_event


@pytest.fixture
def child_event_of_source_in_db(loop, child_event_of_source, db):
    loop.run_until_complete(db.event.save(child_event_of_source))
    return child_event_of_source


@pytest.fixture
def update_event_in_db(loop, update_event, db, patch_update_time):
    loop.run_until_complete(db.event.save(update_event))
    return update_event


@pytest.fixture
def eventdb(start_time, end_time, update_time):
    cfg = {
        "id": "5498d53c5f2d60095267a0bb",
        "detail_urls": {"jira": "http://jira", "graphite": "http://graphite"},
        "description": "This is a trigger_deploy event.",
        "time": [start_time, end_time],
        "update_time": update_time,
        "tags": [
            "parent_id:111f1f77bcf86cd799439011",
            "source_id:222f1f77bcf86cd799439011",
            "author:user@example.com",
            "environment:monitor_candidate",
            "environment:monitor_live",
            "services:tycho",
            "source:deploy",
            "status:success",
            "type:deploy/deploy_all"
          ]
        }
    return CATTRS_CONVERTER.structure(cfg, ModelEventDB)
