"""
Firebase Messaging with cone

docs see:
https://firebase.google.com/docs/cloud-messaging/send-message
"""
from cone.firebase.management import get_device_tokens_for_user
from cone.firebase.management import unregister_device_token_for_user
from firebase_admin.exceptions import InvalidArgumentError
from firebase_admin.messaging import UnregisteredError
from typing import Any
import firebase_admin
import logging


logger = logging.getLogger('cone.firebase')


def send_message(data: dict[str, Any], token: str) -> str:
    messaging = firebase_admin.messaging
    message = messaging.Message(data=data, token=token)
    response = messaging.send(message)
    return response


def send_messages(data: dict[str, Any], tokens: list[str]):
    messaging = firebase_admin.messaging
    message = messaging.MulticastMessage(data=data, tokens=tokens)
    response = messaging.send_multicast(message)
    return response


def send_message_to_user(login: str, data: dict[str, Any]) -> list[str]:
    tokens = get_device_tokens_for_user(login)
    results = []
    # return send_messages(data, tokens)
    for token in tokens:
        try:
            res = send_message(data, token)
            results.append(res)
        except (UnregisteredError, InvalidArgumentError):
            unregister_device_token_for_user(login, token)
            logger.exception(f"error sending message to:{token}. the token is not registered in firebase, will be automatically unregistered")
        except Exception:
            logger.exception(f"message to token {token} failed")
            raise

    return results
