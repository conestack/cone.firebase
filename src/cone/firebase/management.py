from cone.app import ugm_backend
from cone.ugm.events import UserCreatedEvent
from cone.ugm.events import UserDeletedEvent
from cone.ugm.events import UserModifiedEvent
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError
from pyramid.security import remember
from yafowil.base import ExtractionError
from zope.event import classhandler
import cone.firebase


FIREBASE_DEVICE_TOKENS = "firebase_device_tokens"


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
            cone.firebase.logger.warning(f"user {uid} has no email -> not added to firebase")


# Registered by call, ``classhandler.handler`` used as decorator returns
# itself instead of the handler function.
classhandler.handler(UserCreatedEvent, on_user_created)


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
    user.attrs["login"] = "mail"
    return user_record


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
            cone.firebase.logger.warning(f"user wth id {uid} not found in firebase, creating it in fb")
            if not user.attrs["fullname"]:
                raise ExtractionError("Fullname not given")
            fbuser = create_firebase_user(user, event.password)
            cone.firebase.logger.warning(f"created user wth id {uid} in fb")
        else:
            fbuser = None
            cone.firebase.logger.warning(f"user wth id {uid} not found in firebase")

    if email and fbuser:
        fullname = user.attrs["fullname"]

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
        cone.firebase.logger.warning(f"user {uid} has no email -> not added to firebase")


classhandler.handler(UserModifiedEvent, on_user_modified)


def on_user_deleted(event):
    user = event.principal
    uid = user.attrs["id"]
    try:
        auth.get_user(uid)
        auth.delete_user(uid)
        cone.firebase.logger.info(f"user with id {uid} deleted in firebase")
    except UserNotFoundError:
        cone.firebase.logger.warning(f"user with id {uid} not found in firebase -> user not deleted in fb")


classhandler.handler(UserDeletedEvent, on_user_deleted)


def authenticate_with_id_token(request, id_token: str) -> tuple[str, str]:
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


def _user_for_login(login: str):
    """Return the user for login, or ``None`` if no such user exists.

    :param login: email or uid
    """
    users = ugm_backend.ugm.users
    uid = login if login in users else users.id_for_login(login)
    return users[uid] if uid in users else None


def register_device_token_for_user(login: str, token: str) -> list[str]:
    """
    registers a device token for a given user
    :param login: email or uid
    :param token: firebase device token
    """
    user = _user_for_login(login)
    if user is None:
        raise KeyError(f"No user for login '{login}'")
    tokens = user.attrs.get(FIREBASE_DEVICE_TOKENS, []) or []
    if token not in tokens:
        user.attrs[FIREBASE_DEVICE_TOKENS] = list(tokens) + [token]

    return user.attrs[FIREBASE_DEVICE_TOKENS]


def unregister_device_token_for_user(login: str, token: str):
    """
    unregisters a device token for a given user. Nothing to do if no user
    exists for login.
    :param login: email or uid
    :param token: firebase device token
    """
    user = _user_for_login(login)
    if user is None:
        return
    tokens = user.attrs.get(FIREBASE_DEVICE_TOKENS, []) or []
    if token in tokens:
        user.attrs[FIREBASE_DEVICE_TOKENS] = [tok for tok in tokens if token != tok]


def get_device_tokens_for_user(login: str) -> list[str]:
    user = _user_for_login(login)
    if user is None:
        return []
    return user.attrs.get(FIREBASE_DEVICE_TOKENS, []) or []
