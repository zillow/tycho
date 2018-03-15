from .event import (add_event_api, add_statics)
from aiohttp_transmute import add_swagger


def add_routes(app):
    # add apis
    add_event_api(app)
    add_statics(app)
    add_swagger(app, "/api/swagger.json", "/api/")
