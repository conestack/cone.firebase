from cone.app import main_hook
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
    from cone import firebase
    firebase.config = FirebaseConfig(
        settings['firebase.web_api_key'],
        settings['firebase.service_account_json_file']
    )


@main_hook
def initialize_firebase(config, global_config, settings):
    load_firebase_config(settings)
