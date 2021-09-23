from typing import Tuple, List

from cone.app import ugm_backend
from cone.ugm.events import UserCreatedEvent, UserModifiedEvent, UserDeletedEvent
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError
from pyramid.security import remember
from yafowil.base import ExtractionError
from zope.event import classhandler
import cone.firebase

FIREBASE_DEVICE_TOKENS = "firebase_device_tokens"


@classhandler.handler(UserCreatedEvent)
def on_user_created(event: UserCreatedEvent):
    user = event.principal
    email = user.attrs["mail"]
    uid = user.attrs["id"]
    # if firebase_user checkbox is not installed, we want to add all users to FB
    if "firebase_user" not in user.attrs or user.attrs["firebase_user"]:
        if email:
            user_record = create_firebase_user(user, event.password)
            cone.firebase.logger.info(f"user {uid} added to firebase with email {email} -> {user_record.__dict__}")
        else:
            cone.firebase.logger.warn(f"user {uid} has no email -> not added to firebase")


def create_firebase_user(user, password):
    fullname = user.attrs["fullname"]
    user_record = auth.create_user(
        uid=user.attrs["id"],
        email=user.attrs["mail"],
        # phone_number='+15555550100',
        # email_verified=True,
        password=password,
        display_name=fullname,
        # photo_url='http://www.example.com/12345678/photo.png',
        disabled=False
    )
    return user_record


@classhandler.handler(UserModifiedEvent)
def on_user_modified(event: UserModifiedEvent):
    user = event.principal
    email = user.attrs["mail"]
    uid = user.attrs["id"]
    try:
        fbuser = auth.get_user(uid)
    except UserNotFoundError:
        # user does not exist in firebase, lets push it to fb, the password has to be specified by hand, otherwise the
        # hashed password will be set in fb!
        if user.attrs.get("firebase_user", False):
            cone.firebase.logger.warn(f"user wth id {uid} not found in firebase, creating it in fb")
            if not user.attrs["fullname"]:
                raise ExtractionError("Fullname not given")
            fbuser = create_firebase_user(user, event.password)
            cone.firebase.logger.warn(f"created user wth id {uid} in fb")
        else:
            fbuser = None
            cone.firebase.logger.warn(f"user wth id {uid} not found in firebase")

    if email and fbuser:
        fullname = user.attrs["fullname"]
        password = event.password

        params = dict(
            email=email,
            # phone_number='+15555550100',
            display_name=fullname,
            disabled=False)

        if event.password:
            params["password"] = event.password

        res = auth.update_user(
            uid,
            **params
        )
        cone.firebase.logger.info(f"user {uid} changes promoted to firebase with email {email} -> {res}")
    else:
        cone.firebase.logger.warn(f"user {uid} has no email -> not added to firebase")


@classhandler.handler(UserDeletedEvent)
def on_user_deleted(event):
    user = event.principal
    uid = user.attrs["id"]
    try:
        fbuser = auth.get_user(uid)
        auth.delete_user(uid)
        cone.firebase.logger.info(f"user with id {uid} deleted in firebase")
    except UserNotFoundError:
        cone.firebase.logger.warn(f"user with id {uid} not found in firebase -> user not deleted in fb")


def authenticate_with_id_token(request, id_token: str) -> Tuple[str, str]:
    """
    uses the firebase ID token to login without password
    needs installed UGM user folder located at AppRoot()["users"]

    :return: tuple (user_id, auth token)
    """
    # users = AppRoot()["users"]
    cone.firebase.logger.info(f"loggin in with firebase id token: {id_token}")
    ugm = ugm_backend.ugm
    users = ugm.users
    res = auth.verify_id_token(id_token)
    user_id = res["user_id"]
    if user_id not in users:
        # TODO: creation shall take place in security.authenticate()
        cone.firebase.logger.info(f"user with id {user_id} not stored locally - creating")
        users.create(
            user_id,
            login="email",
            email=res["email"],
            fullname=res.get("name", ""),
            email_verified=res["email_verified"],
            phone=res.get("phone_number", ""),
            idtoken=id_token
        )
        cone.firebase.logger.info(f"user with {user_id} successfully created")

    return user_id, remember(request, user_id)


def register_device_token_for_user(login: str, token: str) -> List[str]:
    """
    registers a device token for a given user
    :param login: email or uid
    :param token: firebase device token
    """
    users = ugm_backend.ugm.users
    if login not in users:
        uid = users.id_for_login(login)
    else:
        uid = login

    user = users[uid]
    tokens = user.attrs.get(FIREBASE_DEVICE_TOKENS, []) or []
    if token not in tokens:
        user.attrs[FIREBASE_DEVICE_TOKENS] = list(tokens) + [token]

    return user.attrs[FIREBASE_DEVICE_TOKENS]


def unregister_device_token_for_user(login: str, token: str):
    """
    registers a device token for a given user
    :param login: email or uid
    :param token: firebase device token
    """
    users = ugm_backend.ugm.users
    if login not in users:
        uid = users.id_for_login(login)
    else:
        uid = login

    user = users[uid]
    tokens = user.attrs.get(FIREBASE_DEVICE_TOKENS, []) or []
    if token in tokens:
        user.attrs[FIREBASE_DEVICE_TOKENS] = [tok for tok in tokens if token != tok]


def get_device_tokens_for_user(login: str) -> List[str]:
    users = ugm_backend.ugm.users
    if login not in users:
        uid = users.id_for_login(login)
    else:
        uid = login

    if uid in users:
        user = users[uid]
        return user.attrs.get(FIREBASE_DEVICE_TOKENS, []) or []
    else:
        return []
