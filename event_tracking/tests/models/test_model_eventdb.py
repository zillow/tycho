import pytest
import bson
import datetime
from event_tracking.models.eventdb import EventDB
from schematics.contrib.mongo import ObjectIdType
from schematics.exceptions import DataError
from schematics.models import Model


def test_objectidtype_object_empty():
    obj = ObjectIdType()
    with pytest.raises(TypeError):
        obj("507f1f77bcf86cd7994390112")


def test_objectidtype_on_invalid_objectid():
    obj = ObjectIdType()
    with pytest.raises(TypeError):
        obj.validate("123")


def test_objectidtype_on_objectd():
    obj = ObjectIdType()
    try:
        obj.validate(bson.ObjectId("507f1f77bcf86cd799439011"))
    except pytest.raises(TypeError):
        pytest.fail("This exception shouldn't be raised")


def test_objectidtype_errors_at_non_objectid():
    class SubModel(Model):
        _id = ObjectIdType(required=False)
    doc = {"_id": "123"}
    with pytest.raises(DataError):
        # when illegal value present. init raise exception.
        SubModel(doc)


def test_eventdb_no_field_present():
    doc = {}
    # when no illegal value present.
    # below initialization won't raise exception.
    event = EventDB(doc)
    with pytest.raises(DataError):
        event.validate()


def test_eventdb_required_fields_not_present():
    doc = {"detail_urls": {"graphite": "http://graphite",
           "concrete": "http://concrete"}}
    event = EventDB(doc)
    with pytest.raises(DataError):
        event.validate()


def test_eventdb_required_fields_present():
    doc = {"_id": "507f1f77bcf86cd799439011",
           "update_time": datetime.datetime.utcnow(),
           "time": [datetime.datetime.utcnow()]}
    event = EventDB(doc)
    try:
        event.validate()
    except pytest.raises(DataError):
        pytest.fail("This exception shouldn't be raised")


def test_eventdb_all_fields_present():
    doc = {"_id": "507f1f77bcf86cd799439011",
           "time": [datetime.datetime.utcnow()],
           "update_time": datetime.datetime.utcnow(),
           "detail_urls": {"graphite": "http://graphite"},
           "tags": ["author:yusuket"]}
    event = EventDB(doc)
    try:
        event.validate()
    except pytest.raises(DataError):
        pytest.fail("This exception shouldn't be raised")
