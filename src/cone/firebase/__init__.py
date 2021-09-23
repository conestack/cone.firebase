from cone.app import main_hook
from cone.app.interfaces import IAuthenticator
from cone.firebase.authentication import FirebaseAuthenticator
from cone.ugm.browser.principal import user_field
from yafowil.base import factory
import firebase_admin
import json
import logging


logger = logging.getLogger('cone.firebase')


class FirebaseConfig(object):
    web_api_key = None
    service_account_json = None

    def __init__(self, web_api_key, service_account_json_file):
        self.web_api_key = web_api_key
        with open(service_account_json_file, 'r') as f:
            self.service_account_json = json.loads(f.read())


# FirebaseConfig singleton
config = None


def load_firebase_config(settings):
    global config
    config = FirebaseConfig(
        settings['firebase.web_api_key'],
        settings['firebase.service_account_json_file']
    )


def initialize_firebase_admin():
    service_account_json = config.service_account_json
    cred = firebase_admin.credentials.Certificate(service_account_json)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)


@user_field('firebase_user')
def firebase_user_field_factory(form, label, value):
    return factory(
        'field:label:help:error:checkbox',
        value=value,
        props={
            'label': label,
            'datatype': bool,
            'help': "shall this user also be managed in Firebase?",
        })


@user_field('fullname')
def fullname_field_factory(form, label, value):
    return factory(
        'field:label:error:text',
        value=value,
        props={
            'label': label,
            'datatype': str,
            'required': "fullname not given"
        })


@main_hook
def initialize_firebase(config, global_config, settings):
    load_firebase_config(settings)
    initialize_firebase_admin()
    config.registry.registerUtility(
        FirebaseAuthenticator,
        IAuthenticator,
        'firebase'
    )
