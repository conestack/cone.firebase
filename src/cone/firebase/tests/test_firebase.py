from cone import firebase
from cone.app.ugm import ugm_backend
from cone.firebase import authentication
from cone.firebase import management
from cone.firebase import messaging
from cone.firebase import testing
from cone.firebase.api import get_device_tokens_for_user
from cone.firebase.api import register_device_token_for_user
from cone.firebase.testing import firebase_admin
from cone.firebase.testing.firebase_admin import messaging as fb_fake_messaging
from cone.ugm.events import UserCreatedEvent
from cone.ugm.events import UserDeletedEvent
from cone.ugm.events import UserModifiedEvent
from firebase_admin.auth import UserNotFoundError
from firebase_admin.exceptions import InvalidArgumentError
from firebase_admin.messaging import UnregisteredError
from node.tests import NodeTestCase
from unittest import mock
from yafowil.base import ExtractionError
from zope.event import classhandler
from zope.event import notify
import json


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
        authenticator = security.AUTHENTICATOR
        security.AUTHENTICATOR = "firebase"
        try:
            security.authenticate(request, "donald@duck.com", "daisy1")
            # during the authentication the user should be added to UGM
            self.assertTrue("donald" in users)
        finally:
            security.AUTHENTICATOR = authenticator
            if "donald" in users:
                del users["donald"]

    def test_local_authentication(self):
        """Tests a local only login for the situation that a certain user is
        only given locally and login should the fall back to standard auth
        """
        from cone.app import security
        users = ugm_backend.ugm.users
        self.assertTrue("donald_local" in users)

        request = self.layer.new_request()
        authenticator = security.AUTHENTICATOR
        security.AUTHENTICATOR = "firebase"
        try:
            self.assertTrue(
                security.authenticate(request, "donald_local", "daisy1")
            )
        finally:
            security.AUTHENTICATOR = authenticator

    def tearDown(self):
        user = ugm_backend.ugm.users['donald_local']
        user.attrs[management.FIREBASE_DEVICE_TOKENS] = []
        super().tearDown()

    def test_management(self):
        """Test management of device tokens for firebase messaging
        """
        register_device_token_for_user("donald_local", EXAMPLE_DEVICE_TOKEN)
        self.assertTrue(
            EXAMPLE_DEVICE_TOKEN in get_device_tokens_for_user("donald_local")
        )

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
        register_device_token_for_user("donald_local", EXAMPLE_DEVICE_TOKEN)
        data = {'score': '850', 'time': '2:45'}
        res = messaging.send_message_to_user("donald_local", data)
        self.assertTrue(res[0].startswith('projects/willholzen-293208/messages/'))


class FakePrincipal:

    def __init__(self, **attrs):
        self.attrs = attrs


class TestFirebaseUserFields(NodeTestCase):
    layer = testing.firebase_layer

    def test_firebase_user_field_is_checkbox(self):
        widget = firebase.firebase_user_field_factory(None, 'FB user', True)
        self.assertEqual(widget.blueprints, [
            'field', 'label', 'help', 'error', 'checkbox'
        ])
        self.assertTrue(widget.getter)
        self.assertEqual(widget.properties['label'], 'FB user')
        self.assertIs(widget.properties['datatype'], bool)

    def test_email_verified_field_is_checkbox(self):
        widget = firebase.email_verified(None, 'Verified', False)
        self.assertEqual(widget.blueprints, [
            'field', 'label', 'help', 'error', 'checkbox'
        ])
        self.assertFalse(widget.getter)
        self.assertEqual(widget.properties['label'], 'Verified')

    def test_fullname_field_is_required_text(self):
        widget = firebase.fullname_field_factory(None, 'Fullname', 'Donald')
        self.assertEqual(widget.blueprints, [
            'field', 'label', 'error', 'text'
        ])
        self.assertEqual(widget.getter, 'Donald')
        self.assertEqual(
            widget.properties['required'],
            'fullname not given'
        )


class TestAuthentication(NodeTestCase):
    layer = testing.firebase_layer

    @property
    def sign_in(self):
        # the layer replaces the module function with a fake
        return self.layer.sign_in_with_email_and_password

    def test_sign_in_posts_credentials_to_firebase_rest_api(self):
        with mock.patch.object(authentication, 'requests') as requests:
            requests.post.return_value.json.return_value = {'kind': 'x'}
            res = self.sign_in('donald@duck.com', 'daisy1', 'apikey')
        self.assertEqual(res, {'kind': 'x'})
        requests.post.assert_called_once_with(
            authentication.REST_API_URL_LOGIN,
            params={'key': 'apikey'},
            data=json.dumps({
                'email': 'donald@duck.com',
                'password': 'daisy1',
                'returnSecureToken': True
            })
        )

    def test_sign_in_sends_empty_strings_for_missing_credentials(self):
        with mock.patch.object(authentication, 'requests') as requests:
            self.sign_in(None, None, 'apikey', return_secure_token=False)
        payload = json.loads(requests.post.call_args.kwargs['data'])
        self.assertEqual(payload, {
            'email': '',
            'password': '',
            'returnSecureToken': False
        })

    def test_sign_in_logs_encoding_error_without_password_and_reraises(self):
        with mock.patch.object(authentication, 'requests') as requests:
            with self.assertLogs('cone.firebase', 'ERROR') as logs:
                with self.assertRaises(TypeError):
                    self.sign_in(
                        'donald@duck.com',
                        'secret',
                        'apikey',
                        return_secure_token=object()
                    )
        requests.post.assert_not_called()
        self.assertEqual(len(logs.output), 1)
        self.assertIn('donald@duck.com', logs.output[0])
        self.assertNotIn('secret', logs.output[0])

    def test_authenticate_notifies_users_about_firebase_login(self):
        users = ugm_backend.ugm.users
        firebase_admin.create_user(
            uid='daisy',
            email='daisy@duck.com',
            displayName='Daisy Duck'
        )
        try:
            with mock.patch.object(
                users,
                'on_authenticated',
                create=True
            ) as on_authenticated:
                uid = authentication.FirebaseAuthenticator.authenticate(
                    'daisy@duck.com',
                    'secret'
                )
            self.assertEqual(uid, 'daisy')
            on_authenticated.assert_called_once_with('daisy')
            self.assertEqual(users['daisy'].attrs['fullname'], 'Daisy Duck')
        finally:
            firebase_admin.delete_user('daisy')
            if 'daisy' in users:
                del users['daisy']

    def test_authenticate_falls_back_to_local_ugm(self):
        uid = authentication.FirebaseAuthenticator.authenticate(
            'donald_local',
            'daisy1'
        )
        self.assertEqual(uid, 'donald_local')

    def test_authenticate_returns_none_for_invalid_local_credentials(self):
        uid = authentication.FirebaseAuthenticator.authenticate(
            'donald_local',
            'wrong'
        )
        self.assertIsNone(uid)


class TestUserEventHandlers(NodeTestCase):
    layer = testing.firebase_layer

    def test_handlers_are_registered_for_user_events(self):
        registry = classhandler.registry
        self.assertIn(management.on_user_created, registry[UserCreatedEvent])
        self.assertIn(
            management.on_user_modified,
            registry[UserModifiedEvent]
        )
        self.assertIn(management.on_user_deleted, registry[UserDeletedEvent])

    def test_handlers_can_be_called_directly(self):
        user = FakePrincipal(id='daisy', mail='', firebase_user=True)
        with self.assertLogs('cone.firebase', 'WARNING') as logs:
            management.on_user_created(UserCreatedEvent(user))
        self.assertIn('user daisy has no email', logs.output[0])

    def test_user_created_creates_firebase_user(self):
        user = FakePrincipal(
            id='daisy',
            mail='daisy@duck.com',
            fullname='Daisy Duck'
        )
        event = UserCreatedEvent(user, password='secret')
        with mock.patch.object(management, 'auth') as auth:
            notify(event)
        auth.create_user.assert_called_once_with(
            uid='daisy',
            email='daisy@duck.com',
            password='secret',
            display_name='Daisy Duck',
            disabled=False
        )
        self.assertEqual(user.attrs['login'], 'mail')

    def test_user_created_skips_firebase_if_not_firebase_user(self):
        user = FakePrincipal(
            id='daisy',
            mail='daisy@duck.com',
            firebase_user=False
        )
        with mock.patch.object(management, 'auth') as auth:
            notify(UserCreatedEvent(user))
        auth.create_user.assert_not_called()

    def test_user_created_without_email_is_not_added_to_firebase(self):
        user = FakePrincipal(id='daisy', mail='', firebase_user=True)
        with mock.patch.object(management, 'auth') as auth:
            with self.assertLogs('cone.firebase', 'WARNING') as logs:
                notify(UserCreatedEvent(user))
        auth.create_user.assert_not_called()
        self.assertIn('user daisy has no email', logs.output[0])

    def test_user_modified_promotes_changes_to_firebase(self):
        fb_user = firebase_admin.create_user(email='daisy@duck.com')
        uid = fb_user.uid
        self.assertEqual(uid, 'daisy@duck.com')
        user = FakePrincipal(id=uid, mail=uid, fullname='Daisy Duck')
        try:
            notify(UserModifiedEvent(user, password='secret'))
            fb_user = firebase_admin.get_user(uid)
            self.assertEqual(fb_user.display_name, 'Daisy Duck')
            self.assertFalse(fb_user.disabled)
            self.assertEqual(
                firebase_admin.users_by_id[uid]['password'],
                'secret'
            )
        finally:
            firebase_admin.delete_user(uid)

    def test_user_modified_without_password_keeps_firebase_password(self):
        user = FakePrincipal(
            id='daisy',
            mail='daisy@duck.com',
            fullname='Daisy Duck'
        )
        with mock.patch.object(management, 'auth') as auth:
            notify(UserModifiedEvent(user))
        auth.update_user.assert_called_once_with(
            'daisy',
            email='daisy@duck.com',
            display_name='Daisy Duck',
            disabled=False
        )

    def test_user_modified_creates_missing_firebase_user(self):
        user = FakePrincipal(
            id='daisy',
            mail='daisy@duck.com',
            fullname='Daisy Duck',
            firebase_user=True
        )
        with mock.patch.object(management, 'auth') as auth:
            auth.get_user.side_effect = UserNotFoundError('not found')
            notify(
                UserModifiedEvent(user, password='secret')
            )
        auth.create_user.assert_called_once_with(
            uid='daisy',
            email='daisy@duck.com',
            password='secret',
            display_name='Daisy Duck',
            disabled=False
        )
        auth.update_user.assert_called_once()

    def test_user_modified_requires_fullname_for_missing_firebase_user(self):
        user = FakePrincipal(
            id='daisy',
            mail='daisy@duck.com',
            fullname='',
            firebase_user=True
        )
        with mock.patch.object(management, 'auth') as auth:
            auth.get_user.side_effect = UserNotFoundError('not found')
            with self.assertRaises(ExtractionError):
                notify(UserModifiedEvent(user))
        auth.create_user.assert_not_called()

    def test_user_modified_ignores_missing_non_firebase_user(self):
        user = FakePrincipal(
            id='daisy',
            mail='daisy@duck.com',
            fullname='Daisy Duck'
        )
        with mock.patch.object(management, 'auth') as auth:
            auth.get_user.side_effect = UserNotFoundError('not found')
            with self.assertLogs('cone.firebase', 'WARNING') as logs:
                notify(UserModifiedEvent(user))
        auth.create_user.assert_not_called()
        auth.update_user.assert_not_called()
        self.assertIn('daisy not found in firebase', logs.output[0])

    def test_user_deleted_deletes_firebase_user(self):
        firebase_admin.create_user(uid='daisy', email='daisy@duck.com')
        user = FakePrincipal(id='daisy')
        try:
            notify(UserDeletedEvent(user))
            self.assertNotIn('daisy', firebase_admin.users_by_id)
            self.assertNotIn('daisy@duck.com', firebase_admin.users_by_email)
        finally:
            firebase_admin.users_by_id.pop('daisy', None)
            firebase_admin.users_by_email.pop('daisy@duck.com', None)

    def test_user_deleted_logs_missing_firebase_user(self):
        user = FakePrincipal(id='daisy')
        with self.assertLogs('cone.firebase', 'WARNING') as logs:
            notify(UserDeletedEvent(user))
        self.assertIn('daisy not found in firebase', logs.output[0])

    def test_layer_registers_handlers_again_after_unregistering(self):
        self.layer.unregister_handlers()
        self.assertNotIn(
            management.on_user_created,
            classhandler.registry[UserCreatedEvent]
        )
        self.layer.register_handlers()
        self.assertIn(
            management.on_user_created,
            classhandler.registry[UserCreatedEvent]
        )


class TestAuthenticateWithIdToken(NodeTestCase):
    layer = testing.firebase_layer

    def test_authenticate_with_id_token_creates_local_user(self):
        users = ugm_backend.ugm.users
        request = self.layer.new_request()
        token_data = {
            'user_id': 'daisy',
            'email': 'daisy@duck.com',
            'name': 'Daisy Duck',
            'email_verified': True,
        }
        try:
            with mock.patch.object(management, 'auth') as auth:
                auth.verify_id_token.return_value = token_data
                user_id, headers = management.authenticate_with_id_token(
                    request,
                    'id-token'
                )
            auth.verify_id_token.assert_called_once_with('id-token')
            self.assertEqual(user_id, 'daisy')
            self.assertTrue(headers)
            user = users['daisy']
            self.assertEqual(user.attrs['email'], 'daisy@duck.com')
            self.assertEqual(user.attrs['fullname'], 'Daisy Duck')
            self.assertEqual(user.attrs['phone'], '')
            self.assertEqual(user.attrs['idtoken'], 'id-token')
        finally:
            if 'daisy' in users:
                del users['daisy']

    def test_authenticate_with_id_token_uses_existing_local_user(self):
        users = ugm_backend.ugm.users
        request = self.layer.new_request()
        with mock.patch.object(management, 'auth') as auth:
            auth.verify_id_token.return_value = {'user_id': 'donald_local'}
            with mock.patch.object(users, 'create') as create:
                user_id, _ = management.authenticate_with_id_token(
                    request,
                    'id-token'
                )
        self.assertEqual(user_id, 'donald_local')
        create.assert_not_called()


class TestDeviceTokens(NodeTestCase):
    layer = testing.firebase_layer

    def tearDown(self):
        user = ugm_backend.ugm.users['donald_local']
        user.attrs[management.FIREBASE_DEVICE_TOKENS] = []
        super().tearDown()

    def test_register_device_token_does_not_duplicate_tokens(self):
        register_device_token_for_user('donald_local', 'token-1')
        tokens = register_device_token_for_user('donald_local', 'token-1')
        self.assertEqual(list(tokens), ['token-1'])

    def test_register_device_token_fails_for_unknown_login(self):
        with self.assertRaises(KeyError) as arc:
            register_device_token_for_user('unknown', 'token-1')
        self.assertEqual(arc.exception.args[0], "No user for login 'unknown'")

    def test_unregister_device_token_removes_token(self):
        register_device_token_for_user('donald_local', 'token-1')
        register_device_token_for_user('donald_local', 'token-2')
        management.unregister_device_token_for_user(
            'donald_local',
            'token-1'
        )
        self.assertEqual(
            list(get_device_tokens_for_user('donald_local')),
            ['token-2']
        )

    def test_unregister_device_token_ignores_unknown_login(self):
        self.assertIsNone(
            management.unregister_device_token_for_user('unknown', 'token')
        )

    def test_device_tokens_of_unknown_user_are_empty(self):
        self.assertEqual(get_device_tokens_for_user('unknown'), [])


class TestMessaging(NodeTestCase):
    layer = testing.firebase_layer

    def tearDown(self):
        user = ugm_backend.ugm.users['donald_local']
        user.attrs[management.FIREBASE_DEVICE_TOKENS] = []
        super().tearDown()

    def test_send_messages_returns_batch_response(self):
        res = messaging.send_messages({'score': '850'}, [EXAMPLE_DEVICE_TOKEN])
        self.assertEqual(res.success_count, 1)
        self.assertEqual(res.failure_count, 0)
        self.assertEqual(len(res.responses), 1)
        response = res.responses[0]
        self.assertTrue(response.message_id.startswith('projects/'))
        self.assertIsNone(response.exception)

    def test_send_messages_rejects_more_than_500_tokens(self):
        with self.assertRaises(ValueError):
            messaging.send_messages({'score': '850'}, ['token'] * 501)

    def test_send_message_to_user_unregisters_invalid_tokens(self):
        for token in ('unregistered', 'invalid', 'valid'):
            register_device_token_for_user('donald_local', token)
        errors = {
            'unregistered': UnregisteredError('unregistered'),
            'invalid': InvalidArgumentError('invalid'),
        }

        def send(message, dry_run=False):
            if message.token in errors:
                raise errors[message.token]
            return f'sent:{message.token}'

        with mock.patch.object(fb_fake_messaging, 'send', send):
            with self.assertLogs('cone.firebase', 'ERROR') as logs:
                res = messaging.send_message_to_user(
                    'donald_local',
                    {'score': '850'}
                )
        self.assertEqual(res, ['sent:valid'])
        self.assertEqual(
            list(get_device_tokens_for_user('donald_local')),
            ['valid']
        )
        self.assertEqual(len(logs.output), 2)

    def test_send_message_to_user_logs_and_reraises_other_errors(self):
        register_device_token_for_user('donald_local', 'token-1')
        send = mock.Mock(side_effect=RuntimeError('boom'))
        with mock.patch.object(fb_fake_messaging, 'send', send):
            with self.assertLogs('cone.firebase', 'ERROR') as logs:
                with self.assertRaises(RuntimeError):
                    messaging.send_message_to_user(
                        'donald_local',
                        {'score': '850'}
                    )
        self.assertIn('message to token token-1 failed', logs.output[0])
        self.assertEqual(
            list(get_device_tokens_for_user('donald_local')),
            ['token-1']
        )
