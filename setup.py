import os
import sys
from setuptools import setup, find_packages

BASE = os.path.dirname(os.path.abspath(__file__))

is_release = False
if "--release" in sys.argv:
    is_release = True
    sys.argv.remove("--release")


setup(name='tycho',
      setup_requires=["vcver", "setuptools-parcels"],
      vcver={"is_release": is_release,
             "path": BASE},
      description='',
      author="zillow-orbital",
      author_email="",
      long_description=open('README.rst').read(),
      packages=find_packages(),
      install_requires=[
          'aiohttp',
          'aiohttp-cors',
          'aiohttp-transmute',
          'motor',
          'pymongo',
          'orbital-core'
      ],
      entry_points={
          'console_scripts': [
              'create_indexes=event_tracking.scripts.create_indexes:main'
          ]
      },
      include_package_data=True,
      parcels={}
)
