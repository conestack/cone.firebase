.. image:: https://img.shields.io/pypi/v/cone.firebase.svg
    :target: https://pypi.python.org/pypi/cone.firebase
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/cone.firebase.svg
    :target: https://pypi.python.org/pypi/cone.firebase
    :alt: Number of PyPI downloads

.. image:: https://github.com/conestack/cone.firebase/actions/workflows/test.yml/badge.svg
    :target: https://github.com/conestack/cone.firebase/actions/workflows/test.yml
    :alt: Test cone.firebase


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

also in your ugm.xml you can optionally add the `firebase_user` checkbox:

.. code-block:: xml

    <users_form_attrmap>
        ...
        <elem>
            <key>firebase_user</key>
            <value>Firebase User</value>
        </elem>
    </users_form_attrmap>

When you want to upgrade an existing user to FB, you can do this by checking
`firebase_user` in the user edit form, butt attention: you have to manually
enter the password since the firebase API expects the password in cleartext.

Contributors
============

- Robert Niederreiter
- Phil Auersperg
