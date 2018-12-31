import asyncio
import os
from tycho.app import create_app
from tycho.models.config import Config

DB_URI = os.environ.get(
    "TYCHO_MONGODB_URI",
    "mongodb://mongo:27017/?maxPoolSize=1&w=1"
)

print(DB_URI)

config = Config({
    "mongo": {
        "uri": DB_URI,
        "db_name": "tycho",
    },
})

loop = asyncio.get_event_loop()
app = create_app(config)
