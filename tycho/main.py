import asyncio
import os
import logging
import yaml
from .app import create_app
from .models.config import Config


def from_yaml(path):
    with open(path) as fh:
        return Config(yaml.load(fh.read()))

ROOT = os.path.dirname(os.path.dirname(__file__))
DEFAULT_CONFIG_PATH = os.path.join(ROOT, "config", "current", "config.yaml")
config_path = DEFAULT_CONFIG_PATH
config = from_yaml(config_path)
app = create_app(config)
