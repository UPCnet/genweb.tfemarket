# -*- coding: utf-8 -*-
"""Installer for the genweb.tfemarket package."""

from setuptools import find_packages, setup
import os

version = '1.4.4'

README = open("README.rst").read()
HISTORY = open(os.path.join("docs", "HISTORY.rst")).read()

setup(
    name='genweb.tfemarket',
    version=version,
    description="TFE market for Genweb UPC",
    long_description=README + "\n" + HISTORY,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='Python Plone',
    author='UPCnet Plone Team',
    author_email='plone.team@upcnet.es',
    url='https://github.com/UPCnet/genweb.tfemarket',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['genweb'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'plone.api',
        'setuptools',
        'plone.app.dexterity',
        'five.grok',
        'collective.dexteritytextindexer',
        'soappy',
        'z3c.saconfig'

    ],
    extras_require={
        'test': [
            'plone.app.testing',
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            'plone.testing>=5.0.0',
            'plone.app.contenttypes',
            'plone.app.robotframework[debug]',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
