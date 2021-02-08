# Fake api for cloud messaging

class Message:
    """A message that can be sent via Firebase Cloud Messaging.

    Contains payload information as well as recipient information. In particular, the message must
    contain exactly one of token, topic or condition fields.

    Args:
        data: A dictionary of data fields (optional). All keys and values in the dictionary must be
            strings.
        notification: An instance of ``messaging.Notification`` (optional).
        android: An instance of ``messaging.AndroidConfig`` (optional).
        webpush: An instance of ``messaging.WebpushConfig`` (optional).
        apns: An instance of ``messaging.ApnsConfig`` (optional).
        fcm_options: An instance of ``messaging.FCMOptions`` (optional).
        token: The registration token of the device to which the message should be sent (optional).
        topic: Name of the FCM topic to which the message should be sent (optional). Topic name
            may contain the ``/topics/`` prefix.
        condition: The FCM condition to which the message should be sent (optional).
    """

    def __init__(self, data=None, notification=None, android=None, webpush=None, apns=None,
                 fcm_options=None, token=None, topic=None, condition=None):
        self.data = data
        self.notification = notification
        self.android = android
        self.webpush = webpush
        self.apns = apns
        self.fcm_options = fcm_options
        self.token = token
        self.topic = topic
        self.condition = condition

    def __str__(self):
        return json.dumps(self, cls=MessageEncoder, sort_keys=True)

class MulticastMessage:
    """A message that can be sent to multiple tokens via Firebase Cloud Messaging.

    Args:
        tokens: A list of registration tokens of targeted devices.
        data: A dictionary of data fields (optional). All keys and values in the dictionary must be
            strings.
        notification: An instance of ``messaging.Notification`` (optional).
        android: An instance of ``messaging.AndroidConfig`` (optional).
        webpush: An instance of ``messaging.WebpushConfig`` (optional).
        apns: An instance of ``messaging.ApnsConfig`` (optional).
        fcm_options: An instance of ``messaging.FCMOptions`` (optional).
    """
    def __init__(self, tokens, data=None, notification=None, android=None, webpush=None, apns=None,
                 fcm_options=None):
        # _Validators.check_string_list('MulticastMessage.tokens', tokens)
        if len(tokens) > 500:
            raise ValueError('MulticastMessage.tokens must not contain more than 500 tokens.')
        self.tokens = tokens
        self.data = data
        self.notification = notification
        self.android = android
        self.webpush = webpush
        self.apns = apns
        self.fcm_options = fcm_options


class BatchResponse:
    """The response received from a batch request to the FCM API."""

    def __init__(self, responses):
        self._responses = responses
        self._success_count = len([resp for resp in responses if resp.success])

    @property
    def responses(self):
        """A list of ``messaging.SendResponse`` objects (possibly empty)."""
        return self._responses

    @property
    def success_count(self):
        return self._success_count

    @property
    def failure_count(self):
        return len(self.responses) - self.success_count


class SendResponse:
    """The response received from an individual batched request to the FCM API."""

    def __init__(self, resp, exception):
        self._exception = exception
        self._message_id = None
        if resp:
            self._message_id = resp.get('name', None)

    @property
    def message_id(self):
        """A message ID string that uniquely identifies the message."""
        return self._message_id

    @property
    def success(self):
        """A boolean indicating if the request was successful."""
        return self._message_id is not None and not self._exception

    @property
    def exception(self):
        """A ``FirebaseError`` if an error occurs while sending the message to the FCM service."""
        return self._exception


def send(message: Message, dry_run=False):
    return 'projects/willholzen-293208/messages/0:1612781129630326%d758af2bf9fd7ecd'


def send_multicast(message: Message, dry_run=False):
    return BatchResponse(
        [
            SendResponse(
                dict(name='projects/willholzen-293208/messages/0:1612781129630326%d758af2bf9fd7ecd'), None)
        ]
    )
