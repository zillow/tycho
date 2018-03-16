import os
from aiohttp import web
from aiohttp_transmute import TransmuteUrlDispatcher
from .routes import add_routes
from .db import init_db as init_db
from orbital_core import bootstrap_app

APP_ROOT = os.path.dirname(os.path.dirname(__file__))


async def create_app(loop, config, **kwargs):
    app = web.Application(loop=loop)
    bootstrap_app(app, APP_ROOT,
                  service_name="tycho",
                  service_description="A change management tracking service")
    add_routes(app)
    app["config"] = config
    app.update(**kwargs)
    app.on_startup.append(lambda app: init_app(app, config))
    return app


async def init_app(app, config):
    if "db" not in app:
        app["db"] = init_db(config.mongo)  # pragma: no cover
