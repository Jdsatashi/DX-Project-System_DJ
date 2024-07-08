from firebase_admin import messaging


def send_firebase_notification(title, body, registration_tokens, data):
    """
    Function to send a Firebase notification with custom data.

    :param title: Title of the notification
    :param body: Body of the notification
    :param registration_tokens: List of device registration tokens
    :param data: Additional custom data to send with the notification
    """
    # Construct the message payload
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        tokens=registration_tokens
    )
    response = messaging.send_multicast(message)
    print('{0} messages were sent successfully'.format(response.success_count))
