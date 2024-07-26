from firebase_admin import messaging

from app.logs import app_log


def send_firebase_notification2(title, body, registration_tokens, data):
    """
    Function to send a Firebase notification with custom data.

    :param title: Title of the notification
    :param body: Body of the notification
    :param registration_tokens: List of device registration tokens
    :param data: Additional custom data to send with the notification
    """
    # Construct the message payload
    app_log.info(f"Hanle upload notify to FIREBASE")
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        tokens=registration_tokens
    )
    response = messaging.send_multicast(message)
    # app_log.info(f"FIREBASE response: {response}")
    # app_log.info('{0} messages were sent successfully'.format(response.success_count))
    return response


def send_firebase_notification(title, body, registration_tokens, data):
    """
    Function to send a Firebase notification with custom data.

    :param title: Title of the notification
    :param body: Body of the notification
    :param registration_tokens: List of device registration tokens
    :param data: Additional custom data to send with the notification
    """
    app_log.info(f"Handling upload notify to FIREBASE")

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        tokens=registration_tokens
    )
    try:
        # response = messaging.send_multicast(message)
        response = messaging.send_each_for_multicast(message)
        app_log.info(f"FIREBASE response: {response}")
        app_log.info('{0} messages were sent successfully'.format(response.success_count))
        return response
    except Exception as e:
        app_log.error(f"Error sending notification to FIREBASE: {e}")
        return None
