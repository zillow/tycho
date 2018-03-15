import asyncio
import docopt
import logging
import pymongo
import pymongo.errors
import sys

# from zonlib.scripts.utils import create_app, get_host_by_db_name
from event_tracking.app import create_app
from event_tracking.app import init_app
# from zonlib.async_db.connection import COLLECTIONS


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


async def create_indexes(app):
    # the check can not be replaced with None check because
    # pymongo/motor returns collection object if any property is missing
    # hence explicitly checking its type as list
    if not isinstance(app['db'].event.indexes, list):
        LOGGER.warn("Collection {0} on {1} has no attribute 'indexes'".format(
            'event', app.async_db.name))
        # not throwing exception here but continue to run script with other
        # valid collections
        return

    for index in app['db'].event.indexes:
        LOGGER.debug(
            "Creating index {0} for {1} collection with unique constraint as {2} \n".format(
                index['keys'], app['db'].event, index['unique'])
        )

        try:
            await app['db'].event.collection.create_index(index['keys'],
                                             unique=index['unique'])
        except pymongo.errors.OperationFailure as e:
            LOGGER.exception(
                "Error occured while creating the index {0} on collection {1}".format(
                    index, 'event')
            )


def main(argv=sys.argv[1:]):
    '''
    Script to create indexes for collections in given DB

    Usage:
        create_indexes
    '''

    loop = asyncio.get_event_loop()

    from event_tracking.main import app

    init_app(app, app['config'])

    loop.run_until_complete(create_indexes(app))
