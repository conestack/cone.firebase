import json
import requests
from zope.interface import implementer
from cone.app.interfaces import IAuthenticator
from cone.app import ugm_backend, security
import cone.firebase

REST_API_URL_LOGIN = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


def sign_in_with_email_and_password(email, password, api_key, return_secure_token = True):
    """
    borrowed from here:
    https://github.com/billydh/python-firebase-admin-sdk-demo/blob/master/sign_in_with_email_and_password.py
    """

    try:
        payload = json.dumps({
            "email": email or "",
            "password": password or "",
            "returnSecureToken": return_secure_token
        })
    except Exception as ex:
        cone.firebase.logger.error(f"error encoding email: {email} and password: {password}")
        raise

    r = requests.post(REST_API_URL_LOGIN,
                      params={"key": api_key},
                      data=payload)

    return r.json()


@implementer(IAuthenticator)
class FirebaseAuthenticator:

    @classmethod 
    def authenticate(cls, uid: str, pwd: str) -> str:
        """
        does firebase authentication and in the case of success
        checks if the uid exists in self.users, if not it creates the user there
        when fb login is unsuccessful delegates it to
        :return: login of logged in user
        """

        res = sign_in_with_email_and_password(uid, pwd, cone.firebase.config.web_api_key)

        ugm = ugm_backend.ugm
        users = ugm.users

        if res.get("kind") == 'identitytoolkit#VerifyPasswordResponse':
            id = res["localId"]
            if id not in users:
                users.create(
                    id,
                    login="email",
                    email=res["email"],
                    fullname=res.get("displayName"),
                    registered=res["registered"],
                    idtoken=res["idToken"]
                )
            # else:
            #    user email aktualisieren

            user = users[id]
            if hasattr(users, "on_authenticated"):
                users.on_authenticated(res["localId"])
            # user.passwd(None, pwd)  # it is to decide if we need local pwds
            return id
        else:
            # if not found in firebase login locally
            auth = users.authenticate(uid, pwd)
            if auth:
                return uid