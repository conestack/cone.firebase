from cone import firebase
from cone.app import testing
from cone.firebase import api
from cone.firebase.testing import firebase_admin
from cone.firebase import authentication
from cone.ugm.testing import UGMLayer, ugm_config, localmanager_config
from cone.app.ugm import ugm_backend
from node.tests import NodeTestCase
import json
import os
import shutil
import sys
import tempfile
import unittest


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

def fake_sign_in_with_email_and_password(email, password, api_key, return_secure_token = True):
    try:
        res = firebase_admin.get_user_by_email(email)
        res["kind"] = 'identitytoolkit#VerifyPasswordResponse'
    except KeyError:
        res = {'error': {'code': 400,
            'message': 'INVALID_EMAIL',
            'errors': [{'message': 'INVALID_EMAIL',
                'domain': 'global',
                'reason': 'invalid'}]}}

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
        firebase_admin.create_user(id="donald", email="donald@duck.com")
        # create a local only user
        users = ugm_backend.ugm.users
        users.create(
                    "donald_local",
                    login="email",
                    email="donald_local@duck.com",
                    fullname="Donald Duck local",
                )
        assert "donald_local" in users

    def tearDown(self):
        self.unpatch_modules()
        super(FirebaseLayer, self).tearDown()
        shutil.rmtree(self.tempdir)
        firebase_admin.delete_user("donald")

    def patch_modules(self):
        self.firebase_admin_orgin = firebase.firebase_admin
        firebase.firebase_admin = firebase_admin
        api.firebase_admin = firebase_admin
        self.sign_in_with_email_and_password = authentication.sign_in_with_email_and_password
        authentication.sign_in_with_email_and_password = fake_sign_in_with_email_and_password

    def unpatch_modules(self):
        firebase.firebase_admin = self.firebase_admin_orgin
        api.firebase_admin = self.firebase_admin_orgin
        authentication.sign_in_with_email_and_password = self.sign_in_with_email_and_password


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
        """
        Tests a login situation where only a firebase user
        exists and after authentication is added to the
        local UGM database
        """
        from cone.app import security
        users = ugm_backend.ugm.users
        request = self.layer.new_request()
        security.AUTHENTICATOR = "firebase"
        aut = security.authenticate(request, "donald@duck.com", "daisy1")

        # during the authentication the user should be added to UGM
        self.assertTrue("donald" in users)

    def test_local_authentication(self):
        """
        Tests a local only login for the situation that a certain user is
        only given locally and login should the fall back to standard auth
        """
        from cone.app import security
        users = ugm_backend.ugm.users
        self.assertTrue("donald_local" in users)

        request = self.layer.new_request()
        security.AUTHENTICATOR = "firebase"
        aut = security.authenticate(request, "donald_local", "daisy1")



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
