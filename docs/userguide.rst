User Guide
==========

Tycho is a service designed for durable storage and fast querying of events that indicate operational
change. Examples of such events include:

* deployments
* work-in-action (upgrading a host, network card)
* AB bucket changes

In short, any change that can affect the behavior of a service.

Once this data is in Tycho, you can perform various queries of the data such as:

* querying a single event
* querying a series of events based on tags and time ranges when the event occurred
* querying for a tree of events: if a parent-child relationship is specified in events,
  Tycho can construct a tree and return the full tree of results.

Tycho is primarily an API, and the primary unit of data is an event. An event might look something like:

.. code-block:: json

  {
      "id": "my-unique-event-id",
      "start_time": "2018-12-31T18:38:52.345000+00:00",
      "end_time": "2018-12-31T18:58:52.345000+00:00",
      "description": "deploy of service foo in environment bar",
      "detail_urls": {
        "deploy": "http://deploy-service/deploy/1"
      },
      "tags": {
        "source": ["deploy"],
        "service": ["foo"],
        "environment": ["bar"]
      }
  }


To describe each component in detail:

* id: a string that unqiuely identifies the event. If omitted, a uuid4 string will be constructed.
* start_time/ end_time: ISO 8601 timestamps of when the event began and ended.
* description: a human-readable description of the event
* detail_urls: a map string/string pairs, with the values being urls.
* tags: a map of string, list of string pairs that are used to index the event.

Submitting Events
*****************

API documentation and a playground are provided at /api/. However, a simple explanation is given here.

Tycho supports two primary APIs for submitting events:

* PUT  to /api/v1/events/, to create new events
* POST to /api/v1/events/, to update existing events

The body should contain the event itself.

Querying Events
***************

Events can be queried by time range and by tags. An example using both looks like:

``/api/v1/event/?tag=environment:production&tag=service:foo&frm=2018-12-31T09:09:25.991Z&page=1``

This will return all events that are tagged with environment:production and service:foo since December 31st, 2018.

Specifying Parent-Child Relationships
*************************************

Oftentimes operational events are automated, such as deploys through a continuous delivery system such as Jenkins or Spinnaker. In those case it may also be valuable to describe
a chain of events that caused the deploy to occur.

To facilitate this, events are able to pass in a parent_id. For example, you could provide the
user-driven commit and the linked deploy object by posting the following:

Parent Event:


.. code-block:: json

  {
    "event": {
        "id": "user-commit-hash",
        "start_time": "2018-12-31T18:18:52.345000+00:00",
        "end_time": "2018-12-31T18:28:52.345000+00:00",
        "description": "",
        "detail_urls": {
          "commit": "http://github.com/deploy/1"
        },
        "tags": {
          "source": ["github"],
          "author": ["myemail@example.com"]
        }
    }
  }


Child Event:

.. code-block:: json

  {
    "event": {
      "id": "my-deploy-event",
      "parent_id": "user-commit-hash",
      "start_time": "2018-12-31T18:38:52.345000+00:00",
      "end_time": "2018-12-31T18:58:52.345000+00:00",
      "description": "deploy of service foo in environment bar",
      "detail_urls": {
        "deploy": "http://deploy-service/deploy/1"
      },
      "tags": {
        "source": ["deploy"],
        "service": ["foo"],
        "environment": ["bar"]
      }
    }
  }


You can then visualize the tree at /event/user-commit-hash/.

In addition, there are various APIs to help you audit event relationships
further. Also available in the API documentation, but a few examples are:

* /api/v1/event/<event_id>/children -> see immediate children of event
* /api/v1/event/<event_id>/impact -> recursively iterate and produce all children
* /api/v1/event/<event_id>/trace -> return the current event, and all parents
