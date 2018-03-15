import os
from setuptools import setup, find_packages

BASE = os.path.dirname(os.path.abspath(__file__))


setup(name='tycho',
      setup_requires=["vcver", "setuptools-parcels"],
      vcver={"path": BASE},
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
          'pyzmq',
          'orbital-core'
      ],
      entry_points={
          'console_scripts': [
              'create_indexes=event_tracking.scripts.create_indexes:main'
          ]
      }
)
