from cone.app import main_hook
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


@main_hook
def initialize_firebase(config, global_config, settings):
    load_firebase_config(settings)
    initialize_firebase_admin()
