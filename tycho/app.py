import os
import logging
from aiohttp import web
from aiohttp_transmute import TransmuteUrlDispatcher
from .routes import add_routes
from .db import init_db as init_db
from orbital_core import bootstrap_app


APP_ROOT = os.path.dirname(__file__)


def create_app(config, **kwargs):
    app = web.Application()
    bootstrap_app(app, APP_ROOT,
                  service_name="tycho",
                  service_description="A service for tracking operational change.")
    add_routes(app)
    # add attributes
    app["config"] = config
    app.update(**kwargs)
    app.on_startup.append(lambda app: init_app(app, config))
    return app


async def init_app(app, config):
    if "db" not in app:
        app["db"] = init_db(config.mongo)  # pragma: no cover
