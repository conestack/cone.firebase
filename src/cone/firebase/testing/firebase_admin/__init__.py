# faking the firebase auth api

from . import credentials  # noqa

_apps = None

users_by_email = {}
users_by_id = {}


def delete_user(uid):
    user = get_user(uid)
    del users_by_email[user["email"]]
    del users_by_id[uid]


def get_user(uid):
    return users_by_id[uid]


def get_user_by_email(email):
    return users_by_email[email]


def update_user(uid, **kw):
    user = users_by_id[uid]
    user.update(**kw)


def create_user(**kw):
    id = kw.pop("id")
    email = kw.pop("email")
    if not id:
        id = email

    new_user = {
        "localId": id,
        "email": email,
        "idToken": "xxx",
        "profilePicture": "",
        "refreshToken": "string",
        "expiresIn": "",
        "registered":True
    }
    new_user.update(**kw)
    users_by_id[new_user["localId"]] = new_user
    users_by_email[new_user["email"]] = new_user
    return new_user


def initialize_app(cred):
    global _apps
    _apps = True
