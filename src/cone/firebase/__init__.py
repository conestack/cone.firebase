from cone.app import main_hook
import logging


logger = logging.getLogger('cone.firebase')


@main_hook
def initialize_firebase(config, global_config, settings):
    # application startup initialization
    # XXX: read ini file config.
    pass
