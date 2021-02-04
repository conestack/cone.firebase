from . import credentials  # noqa

_apps = None


def initialize_app(cred):
    global _apps
    _apps = True
