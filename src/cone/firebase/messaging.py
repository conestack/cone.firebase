"""
Firebase Messaging with cone

docs see:
https://firebase.google.com/docs/cloud-messaging/send-message
"""
from typing import List, Dict, Any
import logging
import firebase_admin
from firebase_admin import messaging
from cone.app import ugm_backend
from cone.firebase.management import get_device_tokens_for_user, unregister_device_token_for_user
from firebase_admin.messaging import UnregisteredError

logger = logging.getLogger('cone.firebase')

def send_message(data: Dict[str, Any], token: str) -> str:
    """

    """
    messaging = firebase_admin.messaging
    message = messaging.Message(data=data, token=token)
    response = messaging.send(message)
    return response


def send_messages(data: Dict[str, Any], tokens: List[str]):
    messaging = firebase_admin.messaging
    message = messaging.MulticastMessage(data=data, tokens=tokens)
    response = messaging.send_multicast(message)
    return response


def send_message_to_user(login: str, data: Dict[str, Any]) -> List[str]:
    tokens = get_device_tokens_for_user(login)
    results = []
    # return send_messages(data, tokens)
    for token in tokens:
        try:
            res = send_message(data, token)
            results.append(res)
        except UnregisteredError as ex:
            unregister_device_token_for_user(login, token)
            logger.exception(f"error sending message to:{token}. the token is not registered in firebase, will be automatically unregistered")
        except Exception as ex:
            logger.exception(f"message to token {token} failed")
            raise

    return results
