# faking the firebase auth api

from . import credentials  # noqa
from . import messaging   # noqa
from firebase_admin.auth import UserNotFoundError

_apps = None

# user data as returned by the firebase REST API sign in
users_by_email = {}
users_by_id = {}


class UserRecord:
    """Fake of ``firebase_admin.auth.UserRecord``."""

    def __init__(self, data):
        self.uid = data["localId"]
        self.email = data["email"]
        self.display_name = data.get("display_name")
        self.disabled = data.get("disabled", False)


def _user_data(uid):
    try:
        return users_by_id[uid]
    except KeyError:
        raise UserNotFoundError(f"No user record found for uid: {uid}")


def delete_user(uid):
    data = _user_data(uid)
    del users_by_email[data["email"]]
    del users_by_id[uid]


def get_user(uid):
    return UserRecord(_user_data(uid))


def get_user_by_email(email):
    return users_by_email[email]


def update_user(uid, **kw):
    data = _user_data(uid)
    data.update(**kw)
    return UserRecord(data)


def create_user(uid=None, email=None, **kw):
    data = {
        "localId": uid or email,
        "email": email,
        "idToken": "xxx",
        "profilePicture": "",
        "refreshToken": "string",
        "expiresIn": "",
        "registered": True
    }
    data.update(**kw)
    users_by_id[data["localId"]] = data
    users_by_email[data["email"]] = data
    return UserRecord(data)


def initialize_app(cred):
    global _apps
    _apps = True
