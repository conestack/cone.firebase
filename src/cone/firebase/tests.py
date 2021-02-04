from cone.app import testing
from cone import firebase
from cone.firebase.testing import firebase_admin
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


class FirebaseLayer(testing.Security):

    def make_app(self, **kw):
        super(FirebaseLayer, self).make_app(**{
            'cone.plugins': 'cone.firebase',
            'firebase.web_api_key': 'xxxxxxxxxx',
            'firebase.service_account_json_file': os.path.join(
                self.tempdir,
                'service_account.json'
            )
        })

    def setUp(self, args=None):
        self.patch_modules()
        self.tempdir = tempfile.mkdtemp()
        with open(os.path.join(self.tempdir, 'service_account.json'), 'w') as f:
            f.write(json.dumps(service_account_json))
        super(FirebaseLayer, self).setUp()

    def tearDown(self):
        self.unpatch_modules()
        super(FirebaseLayer, self).tearDown()
        shutil.rmtree(self.tempdir)

    def patch_modules(self):
        self.firebase_admin_orgin = firebase.firebase_admin
        firebase.firebase_admin = firebase_admin

    def unpatch_modules(self):
        firebase.firebase_admin = self.firebase_admin_orgin


class TestFirebase(NodeTestCase):
    layer = FirebaseLayer()

    def test_initialize_firebase(self):
        self.assertIsInstance(firebase.config, firebase.FirebaseConfig)
        self.assertEqual(firebase.config.web_api_key, 'xxxxxxxxxx')
        self.assertEqual(
            firebase.config.service_account_json,
            service_account_json
        )


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
