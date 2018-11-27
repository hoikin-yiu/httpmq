#!/usr/bin/env python
# encoding: utf-8
from setuptools import setup

readme = open('README.md').read()

setup(
    name='httpmq',
    version='',
    description=readme.partition('\n')[0],
    long_description=readme,
    author_email='hoikin.yiu@gmail.com',
    url='',
    packages=['httpmq'],
    include_package_data=True,
    package_data={},
    install_requires=[
        "aredis==1.1.3",
        "click==6.7",
        "redis==2.10.6",
        "tornado==5.1",
        "uvloop==0.11.3",
    ],
    entry_points={
        "console_scripts": [
            "httpmq=httmp.server:serve",
        ]
    },
)
