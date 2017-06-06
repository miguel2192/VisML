#!/usr/bin/env python

import setuptools
from distutils.core import setup
import versioneer

setup(
    name='VisML',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='Brookhaven National Lab',
    description='A full stack web application framework to couple front-end visualization with back-end machine learning',
    url='http://github.com/celiafish/VisML',
    keywords='Visualization Machine Learning ML',
    license='BSD',
    classifiers=['Development Status :: 1 - Alpha',
                 "License :: OSI Approved :: BSD License",
                 "Programming Language :: Python :: 3.6",
                 "Topic :: Scientific/Engineering :: Computer Science",
                 "Topic :: Software Development :: Libraries",
                 "Intended Audience :: Science/Research",
                 "Intended Audience :: Developers"], install_requires=['flask', 'pymongo', 'bson']
)
