.. event-tracking-service documentation master file, created by
   sphinx-quickstart on Wed Jun  8 10:13:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Tycho's documentation!
==================================================

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

Events must contain a timestamp, and allow an optional description and
arbritrary tags that can be queried from the `API </api/>`_.

Events may also reference a parent event, which ETS can use to
generate a tree display signifying that relationship.

See :doc:`userguide` for more information


Contents:

.. toctree::
   :maxdepth: 2

   userguide
   events
   runbook



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
