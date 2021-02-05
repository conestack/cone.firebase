import firebase_admin

def send_message(data, token):
    messaging = firebase_admin.messaging
    message = messaging.Message(data=data, token=token)
    response = messaging.send(message)
    return response['name']


def send_messages(data, tokens):
    messaging = firebase_admin.messaging
    message = messaging.MulticastMessage(data=data, tokens=tokens)
    response = messaging.send_multicast(message)
    return response['name']
