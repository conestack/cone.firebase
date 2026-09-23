Changes
=======

1.1.1 (unreleased)
------------------

- Do not log the password if encoding the login data fails.
  [rnix]

- Register the user event handlers by calling ``classhandler.handler``. Used
  as decorator it returns itself, so ``on_user_created``, ``on_user_modified``
  and ``on_user_deleted`` were bound to ``zope.event.classhandler.handler``
  and calling them directly silently did nothing.
  [rnix]

- ``unregister_device_token_for_user`` does nothing for an unknown login,
  ``register_device_token_for_user`` raises a ``KeyError`` naming the login.
  Resolving the user for a login is no longer repeated in three functions.
  [rnix]

- ``cone.firebase.testing``: The fake ``firebase_admin`` follows the API of
  ``firebase_admin.auth``. ``create_user`` takes ``uid``, user functions return
  a ``UserRecord`` and raise ``UserNotFoundError`` for an unknown user.
  ``FirebaseLayer`` also patches ``management.auth``, restores everything it
  patches and removes only its own event handlers on tear down.
  [rnix]

- Remove unused imports and variables ruff flags. ``on_user_deleted`` keeps
  the ``auth.get_user`` call, it raises ``UserNotFoundError`` for an unknown
  user. Remove the broken ``Message.__str__`` from the fake ``firebase_admin``
  in ``cone.firebase.testing``.
  [rnix]

- Use ``logger.warning`` instead of the deprecated ``logger.warn``.
  [rnix]

- Modernise the code ruff flags as outdated: ``class X(object)``,
  ``typing.Dict``/``List``/``Tuple`` over builtins, redundant ``open()`` mode.
  Behaviour unchanged. ``super(Class, self)`` is kept, see ``cone.app``.
  [rnix]

- Pin the ruff rule selection in ``pyproject.toml``.
  [rnix]

- Pin ``setuptools<82.0.0`` in ``mx.ini``. ``pyramid`` 2.0.2 still imports
  ``pkg_resources``, which ``setuptools`` 82 removed.
  [rnix]


1.1.0 (2026-02-03)
------------------

- Refactor package layout to use ``pyproject.toml`` and implicit namespace packages.
  [rnix]

- Initial.
  [rnix, zworkb]

