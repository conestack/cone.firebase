from zope.interface import implementer
from cone.app.interfaces import IAuthenticator
from cone.app import ugm_backend, security
import cone.firebase

def sign_in_with_email_and_password(email, password, api_key, return_secure_token = True):
    """
    https://github.com/billydh/python-firebase-admin-sdk-demo/blob/master/sign_in_with_email_and_password.py
    """

    try:
        payload = json.dumps({
            "email": email,
            "password": password,
            "returnSecureToken": return_secure_token
        })
    except Exception as ex:
        logger.error(f"error encoding email: {email} and password: {password}")
        raise

    r = requests.post(REST_API_URL,
                      params={"key": api_key},
                      data=payload)

    return r.json()

@implementer(IAuthenticator)
class FirebaseAuthenticator:

    @classmethod 
    def authenticate(cls, uid, pwd):
        """
        does firebase authentication and in the case of success
        checks if the uid exists in self.users, if not it creates the user there
        when fb login is unsuccessful delegates it to
        """

        res = sign_in_with_email_and_password(uid, pwd, cone.firebase.config.web_api_key)

        if res.get("kind") == 'identitytoolkit#VerifyPasswordResponse':
            ugm = ugm_backend.ugm
            users = ugm.users
            id = res["localId"]
            if id not in users:
                # TODO: creation shall take place in security.authenticate()
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
            return res
        # else:
        #     # if not found in firebase login locally
        #     return self.users.authenticate(uid, pwd)