"""
Firebase Messaging with cone

docs see:
https://firebase.google.com/docs/cloud-messaging/send-message
"""

import firebase_admin
from firebase_admin import messaging
from cone.app import ugm_backend
from cone.firebase.api import get_device_tokens_for_user


def send_message(data, token):
    messaging = firebase_admin.messaging
    message = messaging.Message(data=data, token=token)
    response = messaging.send(message)
    return response['name']


def send_messages(data, tokens):
    messaging = firebase_admin.messaging
    message = messaging.MulticastMessage(data=data, tokens=tokens)
    response = messaging.send_multicast(message)
    return response


def send_message_to_user(login, data):
    tokens = get_device_tokens_for_user(login)
    return send_messages(data, tokens)

