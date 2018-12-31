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
        "start_time": "2018-12-31T18:38:52.345000+00:00",
        "end_time": "2018-12-31T18:58:52.345000+00:00",
        // a string with the description.
        "description": "This is a Concrete event",
        // Links to other systems and services can added to this object.
        // it should contain a single key representing the service or system
        // with more information, and a value with the url to that system.
        //
        // For a large amount of details, it's recommended to store that information
        // in an external service, and use ETS to query for events that point to that
        // information instead.
        "detail_urls": {"graphite": "http//graphite"}
        // tags are an object of <string, array<string>> pairs,
        // signifying all tags that this event matches.
        // this is used for querying.
        //
        // tags have no imposed structure, but some common examples are listed
        // below.
        "tags": {
            # this should be the service or system emitting these events.
            # it helps when trying to find all the events that service recently
            # emitted.
            "source": ["concrete"],
            # this is the type of action. multiple sources can perform the same action.
            # it's important to not tie this to a particular implementation, as
            # technology changes rapidly and the type provides a way to decouple that.
            "type": ["commit"],
            # a list of authors who are responsible for the event.
            # e-mail is a namespace that guarantees uniqueness, and works well
            # alternatively, some other unique key representing the team would
            # work well.
            "author": ["yusuket@example.com", "saroj@example.com"],
            # the list of services this event affects.
            # best practice: only attach this to the event that is actually affecting the service, not
            # the event that will CAUSE an affecting event.
            "service": ["tycho"],
            # pending, fail, success. The event can be updated after the fact,
            # so this can represent some transient state as well.
            # conversely, one could an event after a state change as a separate event.
            "status": ["success"],
            # a bug or ticket number. Having a ticket with work-in-action helps with additional context.
            "bug_number": ["MON-1234"],
        }
    }
