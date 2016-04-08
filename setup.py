#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup


def get_file(fn):
    with open(fn) as fp:
        return fp.read()


requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='socorro_collector',
    version='0.1.0',
    description="Collector for Socorro",
    long_description=(
        get_file('README.rst') +
        '\n\n' +
        get_file('HISTORY.rst')
    ),
    author="Will Kahn-Greene",
    author_email='willkg@mozilla.com',
    url='https://github.com/willkg/socorro_collector',
    packages=[
        'socorro_collector',
    ],
    package_dir={
        'socorro_collector': 'socorro_collector'
    },
    include_package_data=True,
    install_requires=requirements,
    license="MPLv2",
    zip_safe=False,
    keywords='socorro_collector',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
