from cone import firebase
from cone.app.ugm import ugm_backend
from cone.firebase import api
from cone.firebase import authentication
from cone.firebase import messaging
from cone.firebase.api import get_device_tokens_for_user
from cone.firebase.api import register_device_token_for_user
from cone.firebase.testing import firebase_admin
from cone.firebase.testing.firebase_admin import messaging as fb_fake_messaging
from cone.ugm.events import UserCreatedEvent
from cone.ugm.events import UserDeletedEvent
from cone.ugm.events import UserModifiedEvent
from cone.ugm.testing import localmanager_config
from cone.ugm.testing import ugm_config
from cone.ugm.testing import UGMLayer
from node.tests import NodeTestCase
from zope.event import classhandler
import json
import os
import shutil
import sys
import tempfile
import unittest


EXAMPLE_DEVICE_TOKEN = "dtt9cGrcSXicn8mW0tvcTQ:APA91bHlcidOIQwXoXVa3p22fBDvgeu1kUwElEKpdVcliODGAbtjviOV7Ruls2h__enWF1P_gZApIVOOfHKGlTft0vWuzzwGapsXbZIIH9s7-rbpilV4Hu_JzoLBYAwpCoP3Nkf3foPv"


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


def fake_sign_in_with_email_and_password(email, password, api_key,
                                         return_secure_token=True):
    try:
        res = firebase_admin.get_user_by_email(email)
        res["kind"] = 'identitytoolkit#VerifyPasswordResponse'
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
        self.tempdir = tempfile.mkdtemp()
        with open(os.path.join(self.tempdir, 'service_account.json'), 'w') as f:
            f.write(json.dumps(service_account_json))
        super(FirebaseLayer, self).setUp()
        # create a firebase only user
        firebase_admin.create_user(id="donald", login="email", email="donald@duck.com")
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
        firebase.firebase_admin = firebase_admin
        firebase.firebase_admin.messaging = fb_fake_messaging
        api.firebase_admin = firebase_admin
        messaging.firebase_admin = firebase_admin
        self.sign_in_with_email_and_password = authentication.sign_in_with_email_and_password
        authentication.sign_in_with_email_and_password = fake_sign_in_with_email_and_password

    def unpatch_modules(self):
        firebase.firebase_admin = self.firebase_admin_orgin
        api.firebase_admin = self.firebase_admin_orgin
        authentication.sign_in_with_email_and_password = self.sign_in_with_email_and_password

    def unregister_handlers(self):
        del classhandler.registry[UserCreatedEvent]
        del classhandler.registry[UserDeletedEvent]
        del classhandler.registry[UserModifiedEvent]


class TestFirebase(NodeTestCase):
    layer = FirebaseLayer()

    def test_initialize_firebase(self):
        self.assertIsInstance(firebase.config, firebase.FirebaseConfig)
        self.assertEqual(firebase.config.web_api_key, 'xxxxxxxxxx')
        self.assertEqual(
            firebase.config.service_account_json,
            service_account_json
        )

    def test_firebase_authentication(self):
        """Tests a login situation where only a firebase user exists and after
        authentication is added to the local UGM database.
        """
        from cone.app import security
        users = ugm_backend.ugm.users
        request = self.layer.new_request()
        security.AUTHENTICATOR = "firebase"
        security.authenticate(request, "donald@duck.com", "daisy1")

        # during the authentication the user should be added to UGM
        self.assertTrue("donald" in users)

    def test_local_authentication(self):
        """Tests a local only login for the situation that a certain user is
        only given locally and login should the fall back to standard auth
        """
        from cone.app import security
        users = ugm_backend.ugm.users
        self.assertTrue("donald_local" in users)

        request = self.layer.new_request()
        security.AUTHENTICATOR = "firebase"
        security.authenticate(request, "donald_local", "daisy1")

    def test_management(self):
        """Test management of device tokens for firebase messaging
        """
        register_device_token_for_user("donald", EXAMPLE_DEVICE_TOKEN)
        self.assertTrue(EXAMPLE_DEVICE_TOKEN in get_device_tokens_for_user("donald"))

    def test_send_message(self):
        registration_token = EXAMPLE_DEVICE_TOKEN
        message = fb_fake_messaging.Message(
            data={
                'score': '850',
                'time': '2:45',
            },
            token=registration_token,
        )
        res = fb_fake_messaging.send(message, dry_run=True)
        assert res == 'projects/willholzen-293208/messages/0:1612781129630326%d758af2bf9fd7ecd'

    def test_send_multicast_message(self):
        registration_tokens = [EXAMPLE_DEVICE_TOKEN]
        message = fb_fake_messaging.MulticastMessage(
            data={'score': '850', 'time': '2:45'},
            tokens=registration_tokens,
        )
        fb_fake_messaging.send_multicast(message)

    def test_send_message_to_user(self):
        data = {'score': '850', 'time': '2:45'}
        res = messaging.send_message_to_user("donald", data)
        self.assertTrue(res[0].startswith('projects/willholzen-293208/messages/'))


def run_tests():
    from cone.firebase import tests
    from zope.testrunner.runner import Runner

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(tests))

    runner = Runner(found_suites=[suite])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
