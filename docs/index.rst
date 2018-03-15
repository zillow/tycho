.. event-tracking-service documentation master file, created by
   sphinx-quickstart on Wed Jun  8 10:13:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to event-tracking-service's documentation!
==================================================

The `event-tracking-service </>`_ is designed to store and display events
that have occurred over points in time. It is useful to track various
events in a product pipeline:

* builds
* deployments
* operational events
* manual work

Events must contain a timestamp, and allow an optional description and
arbritrary tags that can be queried from the `API </api/>`_.

Events may also reference a parent event, which ETS can use to
generate a tree display signifying that relationship.

See :doc:`events` for more information


Contents:

.. toctree::
   :maxdepth: 2

   events



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
