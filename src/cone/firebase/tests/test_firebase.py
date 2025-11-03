from cone import firebase
from cone.app.ugm import ugm_backend
from cone.firebase import messaging
from cone.firebase import testing
from cone.firebase.api import get_device_tokens_for_user
from cone.firebase.api import register_device_token_for_user
from cone.firebase.testing.firebase_admin import messaging as fb_fake_messaging
from node.tests import NodeTestCase


EXAMPLE_DEVICE_TOKEN = (
    'dtt9cGrcSXicn8mW0tvcTQ:APA91bHlcidOIQwXoXVa3p22fBDvgeu'
    '1kUwElEKpdVcliODGAbtjviOV7Ruls2h__enWF1P_gZApIVOOfHKGl'
    'Tft0vWuzzwGapsXbZIIH9s7-rbpilV4Hu_JzoLBYAwpCoP3Nkf3foPv'
)


class TestFirebase(NodeTestCase):
    layer = testing.firebase_layer

    def test_initialize_firebase(self):
        self.assertIsInstance(firebase.config, firebase.FirebaseConfig)
        self.assertEqual(firebase.config.web_api_key, 'xxxxxxxxxx')
        self.assertEqual(
            firebase.config.service_account_json,
            testing.service_account_json
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
