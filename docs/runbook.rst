Tycho Runbook
=============

Simplest to Try: Docker-Compose
*********************************

Using docker-compose, you can bring up a tycho service and a mongo database
to try tycho out.

A Production Deployment
***********************

Tycho requires a `mongodb <https://www.mongodb.com/>`_ instance to run. Once a
mongo server is up, you can connect the Tycho docker container to it by passing the URI
as the environment variable TYCHO_MONGODB_URI::

  docker run -e "TYCHO_MONGODB_URI=mongodb://localhost:27017" --network=host tycho:latest

Tycho will always use the database name "tycho", and serves at port 8081
