import jinja2
import os

TEMPLATE_DIR = os.path.dirname(__file__)

_cache = {}


def get_template(template_name):
    if template_name not in _cache:
        template_path = os.path.join(TEMPLATE_DIR, template_name)
        with open(template_path) as fh:
            _cache[template_name] = jinja2.Template(fh.read())
    return _cache[template_name]
