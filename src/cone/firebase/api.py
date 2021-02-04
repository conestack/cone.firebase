import firebase_admin


def authenticate(email, password):
    pass


def create_user(email, password, **kw):
    pass


def modify_user(pid, **kw):
    pass


def delete_user(pid):
    pass


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
