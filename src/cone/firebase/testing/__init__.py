from cone import firebase
from cone.app.ugm import ugm_backend
from cone.firebase import api
from cone.firebase import authentication
from cone.firebase import management
from cone.firebase import messaging
from cone.firebase.testing import firebase_admin
from cone.ugm.events import UserCreatedEvent
from cone.ugm.events import UserDeletedEvent
from cone.ugm.events import UserModifiedEvent
from cone.ugm.testing import localmanager_config
from cone.ugm.testing import ugm_config
from cone.ugm.testing import UGMLayer
from zope.event import classhandler
import json
import os
import shutil
import tempfile


service_account_json = {
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'client_email': 'firebase-adminsdk-foo@example.iam.gserviceaccount.com',
    'client_id': 'xxx',
    'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-foo@example.iam.gserviceaccount.com',
    'private_key': '-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----\n',
    'private_key_id': 'xxx',
    'project_id': 'example',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'type': 'service_account'
}


event_handlers = [
    (UserCreatedEvent, management.on_user_created),
    (UserModifiedEvent, management.on_user_modified),
    (UserDeletedEvent, management.on_user_deleted),
]


def fake_sign_in_with_email_and_password(
    email,
    password,
    api_key,
    return_secure_token=True
):
    try:
        res = firebase_admin.get_user_by_email(email)
        res['kind'] = 'identitytoolkit#VerifyPasswordResponse'
    except KeyError:
        res = {
            'error': {
                'code': 400,
                'message': 'INVALID_EMAIL',
                'errors': [{
                    'message': 'INVALID_EMAIL',
                    'domain': 'global',
                    'reason': 'invalid'
                }]
            }
        }
    return res


class FirebaseLayer(UGMLayer):

    def make_app(self):
        ugm_users_file = os.path.join(self.ugm_dir, 'users')
        ugm_groups_file = os.path.join(self.ugm_dir, 'groups')
        ugm_roles_file = os.path.join(self.ugm_dir, 'roles')
        ugm_datadir = os.path.join(self.ugm_dir, 'data')
        # call direct to grandparent
        super(UGMLayer, self).make_app(**{
            'cone.plugins': '\n'.join([
                'cone.ugm',
                'cone.firebase'
            ]),
            'ugm.backend': 'file',
            'ugm.config': ugm_config,
            'ugm.localmanager_config': localmanager_config,
            'ugm.users_file': ugm_users_file,
            'ugm.groups_file': ugm_groups_file,
            'ugm.roles_file': ugm_roles_file,
            'ugm.datadir': ugm_datadir,
            'firebase.web_api_key': 'xxxxxxxxxx',
            'firebase.service_account_json_file': os.path.join(
                self.tempdir,
                'service_account.json'
            )
        })
        ugm_backend.initialize()

    def setUp(self, args=None):
        self.patch_modules()
        self.register_handlers()
        self.tempdir = tempfile.mkdtemp()
        with open(os.path.join(self.tempdir, 'service_account.json'), 'w') as f:
            f.write(json.dumps(service_account_json))
        super(FirebaseLayer, self).setUp()
        # create a firebase only user
        firebase_admin.create_user(uid="donald", login="email", email="donald@duck.com")
        # create a local only user
        users = ugm_backend.ugm.users
        users.create(
            "donald_local",
            login="email",
            email="donald_local@duck.com",
            fullname="Donald Duck local",
        )
        users["donald_local"].passwd(None, "daisy1")
        assert "donald_local" in users

    def tearDown(self):
        self.unpatch_modules()
        self.unregister_handlers()
        super(FirebaseLayer, self).tearDown()
        shutil.rmtree(self.tempdir)
        firebase_admin.delete_user("donald")

    def patch_modules(self):
        self.firebase_admin_orgin = firebase.firebase_admin
        self.auth_orgin = management.auth
        firebase.firebase_admin = firebase_admin
        api.firebase_admin = firebase_admin
        messaging.firebase_admin = firebase_admin
        management.auth = firebase_admin
        self.sign_in_with_email_and_password = authentication.sign_in_with_email_and_password
        authentication.sign_in_with_email_and_password = fake_sign_in_with_email_and_password

    def unpatch_modules(self):
        firebase.firebase_admin = self.firebase_admin_orgin
        api.firebase_admin = self.firebase_admin_orgin
        messaging.firebase_admin = self.firebase_admin_orgin
        management.auth = self.auth_orgin
        authentication.sign_in_with_email_and_password = self.sign_in_with_email_and_password

    def register_handlers(self):
        # handlers get registered on import, re-register after a tear down
        for event_class, handler in event_handlers:
            if handler not in classhandler.registry.get(event_class, []):
                classhandler.handler(event_class, handler)

    def unregister_handlers(self):
        # remove only the own handlers, others may be registered for the same
        # event classes
        for event_class, handler in event_handlers:
            classhandler.registry[event_class].remove(handler)


firebase_layer = FirebaseLayer()
