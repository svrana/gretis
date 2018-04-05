#!/usr/bin/env python

from setuptools import setup
from gretis import __version__

with open('README.md') as f:
    long_description = f.read()
    f.close()

dev_requires = [
    'pylint',
]

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
      extras_require={
          'dev': dev_requires,
      },
)
