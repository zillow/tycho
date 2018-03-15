======
Events
======

Events are the main data that ETS contains, and can be created and
updated.

An event should represent a single manual or automated event, over a
particular period in time.

Events can be updated with brand new data, or merged with existing
data. See the `API </api>`_ for more information.

------------
Event Format
------------

An example event looks like this:

.. code-block:: json

   {
        // a unique ID for your event. This is user-generated,
        // and can include semantic information. maximum 100 characters.
        // in the case where the id is irrelevant, it's recommended to use
        // a uuid4 id, or not pass one at all.
        "id": "333f1f77bcf86cd799439011"
        // if your event was caused by another event being tracked,
        // you may reference it here.
        "parent_id": "111f1f77bcf86cd799439011",
        // all events require a start time and an event time.
        // in the case where is one is not passed, the current time is used.
        // In the case where a single timestamp is passed, it is considered
        //     both the start and end time.
        "start_time": "12/05/16:10:25:00",
        "end_time": "12/05/16:10:26:00",
        // a string with the description.
        "description": "This is a Concrete event",
        // an object containing references that be queried for more information
        // about the event.
        // For a large amount of details, it's recommended to store that information
        // in an external service, and use ETS to query for events that point to that
        // information instead.
        "detail_urls": {"graphite": "http//graphite"}
        // tags are an object of <string, array> pairs,
        // signifying all tags that this event matches.
        // this is useful for querying purposes.
        //
        // tags have no imposed structure, but recommended keys are outlined
        // below.
        "tags": {
            # this should be the source of the event itself, to figure out where things are coming from
            "source": ["concrete"],
            # this is the type of action. multiple sources can perform the same action (e.g. zeploy / shipit for deploy)
            "type": ["commit"],
            # a list of authors who are responsible for the event (should be the e-mail)
            "author": ["yusuket@example.com", "saroj@example.com"],
            # the list of services this event affects. best practice: only attach this to the event that is actually affecting the service, not
            # the event that will CAUSE an affecting event.
            "service": ["zon-web"],
            # pending, fail, success
            "status": ["success"],
            # a concrete hash, if one exists
            "concrete_hash": ["3443333"],
            # the bug number, if it's relevant
            "bug_number": ["MON-1234"],
        }
    }
