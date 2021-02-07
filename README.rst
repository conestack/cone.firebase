.. image:: https://img.shields.io/pypi/v/cone.firebase.svg
    :target: https://pypi.python.org/pypi/cone.firebase
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/cone.firebase.svg
    :target: https://pypi.python.org/pypi/cone.firebase
    :alt: Number of PyPI downloads

.. image:: https://travis-ci.org/bluedynamics/cone.firebase.svg?branch=master
    :target: https://travis-ci.org/bluedynamics/cone.firebase

.. image:: https://coveralls.io/repos/github/bluedynamics/cone.firebase/badge.svg?branch=master
    :target: https://coveralls.io/github/bluedynamics/cone.firebase?branch=master


This package provides a firebase integration in to cone.app.


Installation
------------

Include ``cone.firebase`` to install dependencies in your application's
``setup.py``.


Configuration
-------------

Adopt your application config ini file to define firebase related API keys.

.. code-block:: ini

    [app:my_app]
    use = egg:cone.app#main

    cone.plugins =
        cone.firebase

    cone.authenticator = firebase

    firebase.web_api_key = xxx
    firebase.service_account_json_file = path/to/service_account.json


Contributors
============

- Robert Niederreiter
- Phil Auersperg
