from schematics.models import Model
from schematics.types import StringType, IntType
from schematics.types.compound import ModelType


class Mongo(Model):
    hosts = StringType(required=True)
    replicaset = StringType(required=True)
    db_name = StringType(required=True)
    max_pool_size = StringType(required=True)
    write_concern = StringType(required=True)


class application(Model):
    host = StringType(required=True)
    port = IntType(required=True)


class access_log(Model):
    app = StringType(required=True)


class Config(Model):
    """ a config object that the app accepts. """
    environment = StringType(required=False)
    mongo = ModelType(Mongo, required=True)
    access_log = ModelType(access_log, required=True)
    application = ModelType(application, required=True)