#!/usr/bin/env python
import os
from setuptools import setup
from gretis import __version__


f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
long_description = f.read()
f.close()

setup(name='gretis',
      version=__version__,
      description='Async Redis connection object using Greenlets and Tornado',
      long_description=long_description,
      url='http://github.com/svrana/gretis',
      author='Shaw Vrana',
      author_email='shaw@vranix.com',
      license='MIT',
      packages=['gretis'],
      classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',

      ],
      install_requires=[
          'redis',
          'hiredis',
          'tornado',
          'greenlet',
      ],
      zip_safe=False,
      )
